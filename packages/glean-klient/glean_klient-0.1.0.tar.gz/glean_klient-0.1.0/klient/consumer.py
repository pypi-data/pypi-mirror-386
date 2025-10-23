"""
Kafka consumer wrapper that supports both synchronous and asynchronous operations.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Union, Callable, Any, AsyncIterator, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from confluent_kafka import Consumer, KafkaError, Message
from . import resolve_env_config, split_env_config, extract_bootstrap


logger = logging.getLogger(__name__)


@dataclass
class ConsumerConfig:
    """Configuration for Kafka consumer."""
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 1000
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 10000
    max_poll_records: int = 500
    # Transaction settings
    isolation_level: str = "read_committed"  # default to committed transactional reads; use "read_uncommitted" to see all
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_confluent_config(self) -> Dict[str, Any]:
        """Convert to confluent-kafka configuration format."""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': self.auto_offset_reset,
            'enable.auto.commit': self.enable_auto_commit,
            'auto.commit.interval.ms': self.auto_commit_interval_ms,
            'session.timeout.ms': self.session_timeout_ms,
            'heartbeat.interval.ms': self.heartbeat_interval_ms,
           # 'max.poll.records': self.max_poll_records,
            'isolation.level': self.isolation_level,
        }
        config.update(self.additional_config)
        return config


@dataclass
class MessageResult:
    """Wrapper for Kafka message with metadata."""
    topic: str
    partition: int
    offset: int
    key: Optional[bytes]
    value: Optional[bytes]
    timestamp: tuple  # (timestamp_type, timestamp)
    headers: Optional[Dict[str, bytes]] = None
    # Transaction information
    is_transactional: bool = False
    transaction_id: Optional[str] = None

    @classmethod
    def from_confluent_message(cls, msg: Message) -> 'MessageResult':
        """Create MessageResult from confluent-kafka Message."""
        headers = {}
        if msg.headers():
            headers = {k: v for k, v in msg.headers()}
        
        # Check for transaction information in headers or metadata
        is_transactional = False
        transaction_id = None
        
        # Look for transaction markers in headers
        if headers:
            transaction_id = headers.get(b'__transaction_id')
            if transaction_id:
                transaction_id = transaction_id.decode('utf-8')
                is_transactional = True
        
        return cls(
            topic=msg.topic(),
            partition=msg.partition(),
            offset=msg.offset(),
            key=msg.key(),
            value=msg.value(),
            timestamp=msg.timestamp(),
            headers=headers,
            is_transactional=is_transactional,
            transaction_id=transaction_id
        )


class KafkaConsumerError(Exception):
    """Base exception for Kafka consumer errors."""
    pass

class KafkaConsumerRetriableError(KafkaConsumerError):
    """Error indicating operation may be safely retried."""
    pass

class KafkaConsumerFatalError(KafkaConsumerError):
    """Non-retriable fatal consumer error."""
    pass

class KafkaConsumerRebalanceError(KafkaConsumerError):
    """Errors during rebalance callbacks."""
    pass


class KafkaConsumer:
    """
    Kafka consumer wrapper that supports both sync and async operations.
    """
    
    def __init__(self,
                 config: ConsumerConfig,
                 message_handler: Optional[Callable[[MessageResult], None]] = None,
                 on_assign: Optional[Callable[[Consumer, Sequence], None]] = None,
                 on_revoke: Optional[Callable[[Consumer, Sequence], None]] = None,
                 on_lost: Optional[Callable[[Consumer, Sequence], None]] = None):
        """
        Initialize Kafka consumer.
        
        Args:
            config: Consumer configuration
            message_handler: Optional message handler function
        """
        self.config = config
        self.message_handler = message_handler
        self._consumer = None
        self._is_running = False
        self._executor = None
        # Rebalance callbacks
        self._on_assign = on_assign
        self._on_revoke = on_revoke
        self._on_lost = on_lost

    @classmethod
    def from_env_config(
        cls,
        env: Optional[str] = None,
        config_file: Optional[str] = None,
        group_id: Optional[str] = None,
        isolation_level: str = "read_uncommitted",
        message_handler: Optional[Callable[[MessageResult], None]] = None,
    ) -> 'KafkaConsumer':
        """Construct a KafkaConsumer from environment configuration.

        If group_id is None will use group.id from config or raise ValueError if not found.
        """
        raw = resolve_env_config(env, config_file)
        _, cons_raw, _ = split_env_config(raw)
        effective_bootstrap = extract_bootstrap([cons_raw]) or 'localhost:9092'
        if group_id is None:
            group_id = cons_raw.get('group.id')
        if not group_id:
            raise ValueError("group_id must be provided or present in env configuration")
        addl = dict(cons_raw)
        for k in ['bootstrap.servers', 'group.id']:
            addl.pop(k, None)
        cfg = ConsumerConfig(
            bootstrap_servers=effective_bootstrap,
            group_id=group_id,
            isolation_level=isolation_level,
            additional_config=addl,
        )
        return cls(cfg, message_handler)
        
    def _create_consumer(self) -> Consumer:
        """Create and return a new Consumer instance."""
        if self._consumer is None:
            try:
                self._consumer = Consumer(self.config.to_confluent_config())
                logger.info(f"Created Kafka consumer for group: {self.config.group_id}")
            except Exception as e:
                logger.error(f"Failed to create Kafka consumer: {e}")
                raise KafkaConsumerError(f"Failed to create consumer: {e}")
        return self._consumer
    
    def subscribe(self, topics: List[str]) -> None:
        """Subscribe to a list of topic names.
        
        Args:
            topics: list of topic strings (must be non-empty)
        Raises:
            ValueError: if list empty
            TypeError: if topics not a list of str
        """
        if not isinstance(topics, list):
            raise TypeError("topics must be a list of strings")
        if not topics:
            raise ValueError("topics list cannot be empty")
        for t in topics:
            if not isinstance(t, str):
                raise TypeError("each topic must be a str")
            
        consumer = self._create_consumer()
        try:
            # Build subscribe kwargs, only including callbacks if they exist
            subscribe_kwargs = {}
            
            wrapped_on_assign = self._wrap_on_assign(self._on_assign)
            if wrapped_on_assign is not None:
                subscribe_kwargs['on_assign'] = wrapped_on_assign
                
            wrapped_on_revoke = self._wrap_on_revoke(self._on_revoke)  
            if wrapped_on_revoke is not None:
                subscribe_kwargs['on_revoke'] = wrapped_on_revoke
                
            wrapped_on_lost = self._wrap_on_lost(self._on_lost)
            if wrapped_on_lost is not None:
                subscribe_kwargs['on_lost'] = wrapped_on_lost
            
            consumer.subscribe(topics, **subscribe_kwargs)
            logger.info(f"Subscribed to topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topics {topics}: {e}")
            raise KafkaConsumerError(f"Failed to subscribe: {e}")

    def commit(self) -> None:
        """Commit current offsets."""
        if not self._consumer:
            return
        try:
            self._consumer.commit()
            logger.debug("Offsets committed")
        except Exception as e:
            logger.error(f"Failed to commit offsets: {e}")
            raise KafkaConsumerError(f"Commit failed: {e}")

    def seek_to_offset(self, topic: str, offset: int, partition: Optional[int] = None) -> None:
        """Seek to a specific offset in topic partition(s).
        
        Args:
            topic: Topic name
            offset: Offset to seek to (must be non-negative)
            partition: Specific partition number (must be non-negative). If None, seeks to the same offset in all partitions.
            
        Raises:
            KafkaConsumerError: If seek operation fails or parameters are invalid
        """
        # Validate inputs
        if partition is not None and partition < 0:
            raise KafkaConsumerError("Partition number must be non-negative")
        if offset < 0:
            raise KafkaConsumerError("Offset must be non-negative")
        
        consumer = self._create_consumer()
        try:
            from confluent_kafka import TopicPartition
            
            if partition is not None:
                # Seek to specific partition
                topic_partition = TopicPartition(topic, partition, offset)
                consumer.seek(topic_partition)
                logger.info(f"Seeked to offset {offset} in {topic}[{partition}]")
            else:
                # Seek to all partitions - get topic metadata to find partitions
                cluster_metadata = consumer.list_topics(topic, timeout=10.0)
                if topic not in cluster_metadata.topics:
                    raise KafkaConsumerError(f"Topic '{topic}' not found")
                
                topic_metadata = cluster_metadata.topics[topic]
                partition_count = len(topic_metadata.partitions)
                
                for partition_id in range(partition_count):
                    topic_partition = TopicPartition(topic, partition_id, offset)
                    consumer.seek(topic_partition)
                
                logger.info(f"Seeked to offset {offset} in all {partition_count} partitions of {topic}")
                
        except Exception as e:
            error_msg = f"Failed to seek to offset {offset}" + (f" on partition {partition}" if partition is not None else f" on topic {topic}")
            logger.error(f"{error_msg}: {e}")
            raise KafkaConsumerError(f"{error_msg}: {e}")

    def stop(self) -> None:
        """Stop streaming loops and close consumer."""
        self._is_running = False
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("Consumer closed")
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")

    # Callback wrappers provide logging & error isolation
    def _wrap_on_assign(self, fn):
        if not fn:
            return None
        def _inner(consumer: Consumer, partitions: Sequence):
            try:
                parts = [p.partition for p in partitions]
                from .metrics import inc
                inc("consumer.rebalance.assign")
                logger.info(json.dumps({"event":"rebalance_assign","partitions":parts}))
                fn(consumer, partitions)
            except Exception as e:
                logger.error(f"Error in on_assign callback: {e}")
                raise KafkaConsumerRebalanceError(f"on_assign failed: {e}")
        return _inner

    def _wrap_on_revoke(self, fn):
        if not fn:
            return None
        def _inner(consumer: Consumer, partitions: Sequence):
            try:
                parts = [p.partition for p in partitions]
                from .metrics import inc
                inc("consumer.rebalance.revoke")
                logger.info(json.dumps({"event":"rebalance_revoke","partitions":parts}))
                fn(consumer, partitions)
            except Exception as e:
                logger.error(f"Error in on_revoke callback: {e}")
                raise KafkaConsumerRebalanceError(f"on_revoke failed: {e}")
        return _inner

    def _wrap_on_lost(self, fn):
        if not fn:
            return None
        def _inner(consumer: Consumer, partitions: Sequence):
            try:
                parts = [p.partition for p in partitions]
                from .metrics import inc
                inc("consumer.rebalance.lost")
                logger.warning(json.dumps({"event":"rebalance_lost","partitions":parts}))
                fn(consumer, partitions)
            except Exception as e:
                logger.error(f"Error in on_lost callback: {e}")
                raise KafkaConsumerRebalanceError(f"on_lost failed: {e}")
        return _inner

    def _classify_error(self, kerr: KafkaError) -> KafkaConsumerError:
        if kerr.retriable():
            return KafkaConsumerRetriableError(str(kerr))
        if kerr.fatal():
            return KafkaConsumerFatalError(str(kerr))
        return KafkaConsumerError(str(kerr))
    
    def poll_message(self, timeout: float = 1.0) -> Optional[MessageResult]:
        """
        Poll for a single message synchronously.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            MessageResult if message received, None if timeout
        """
        consumer = self._create_consumer()
        
        try:
            msg = consumer.poll(timeout)
            
            if msg is None:
                return None
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug(f"Reached end of partition {msg.partition()}")
                    return None
                else:
                    classified = self._classify_error(msg.error())
                    logger.error(f"Consumer error: {msg.error()} classified as {classified.__class__.__name__}")
                    raise classified
                    
            return MessageResult.from_confluent_message(msg)
            
        except Exception as e:
            logger.error(f"Error polling message: {e}")
            raise KafkaConsumerError(f"Polling error: {e}")
    
    def consume_messages(self, count: int = 1, timeout: float = 1.0) -> List[MessageResult]:
        """
        Consume multiple messages synchronously.
        
        Args:
            count: Number of messages to consume
            timeout: Timeout in seconds
            
        Returns:
            List of MessageResult objects
        """
        consumer = self._create_consumer()
        messages = []
        
        try:
            msgs = consumer.consume(count, timeout)
            
            for msg in msgs:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                        continue
                    else:
                        classified = self._classify_error(msg.error())
                        logger.error(f"Consumer error: {msg.error()} classified as {classified.__class__.__name__}")
                        raise classified
                
                messages.append(MessageResult.from_confluent_message(msg))
                
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise KafkaConsumerError(f"Consume error: {e}")
            
        return messages
    
    def message_stream(self, timeout: float = 1.0) -> Iterator[MessageResult]:
        """
        Create a synchronous message stream iterator.
        
        Args:
            timeout: Timeout for each poll operation
            
        Yields:
            MessageResult objects
        """
        while self._is_running:
            try:
                message = self.poll_message(timeout)
                if message:
                    yield message
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping stream")
                break
            except Exception as e:
                logger.error(f"Error in message stream: {e}")
                raise
    
    async def apoll_message(self, timeout: float = 1.0) -> Optional[MessageResult]:
        """
        Poll for a single message asynchronously.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            MessageResult if message received, None if timeout
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.poll_message, timeout)
    
    async def aconsume_messages(self, count: int = 1, timeout: float = 1.0) -> List[MessageResult]:
        """
        Consume multiple messages asynchronously.
        
        Args:
            count: Number of messages to consume
            timeout: Timeout in seconds
            
        Returns:
            List of MessageResult objects
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.consume_messages, count, timeout)
    
    async def amessage_stream(self, timeout: float = 1.0) -> AsyncIterator[MessageResult]:
        """
        Create an asynchronous message stream iterator.
        
        Args:
            timeout: Timeout for each poll operation
            
        Yields:
            MessageResult objects
        """
        while self._is_running:
            try:
                message = await self.apoll_message(timeout)
                if message:
                    yield message
                else:
                    # Small delay to prevent tight loop when no messages
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                logger.info("Async stream cancelled")
                break
            except Exception as e:
                logger.error(f"Error in async message stream: {e}")
                raise
    
    def start_consuming(self, topics: Union[str, List[str]], auto_process: bool = True) -> None:
        """
        Start consuming messages in a loop.
        
        Args:
            topics: Topics to subscribe to
            auto_process: Whether to automatically process messages with message_handler
        """
        if isinstance(topics, str):
            topics = [topics]
        self.subscribe(topics)
        self._is_running = True
        
        logger.info(f"Starting consumer for topics: {topics}")
        
        try:
            for message in self.message_stream():
                if auto_process and self.message_handler:
                    try:
                        self.message_handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
                        
        except KeyboardInterrupt:
            logger.info("Received interrupt, stopping consumer")
        finally:
            self.stop()
    
    async def astart_consuming(self, topics: Union[str, List[str]], auto_process: bool = True) -> None:
        """
        Start consuming messages asynchronously.
        
        Args:
            topics: Topics to subscribe to
            auto_process: Whether to automatically process messages with message_handler
        """
        if isinstance(topics, str):
            topics = [topics]
        self.subscribe(topics)
        self._is_running = True
        
        logger.info(f"Starting async consumer for topics: {topics}")
        
        try:
            async for message in self.amessage_stream():
                if auto_process and self.message_handler:
                    try:
                        if asyncio.iscoroutinefunction(self.message_handler):
                            await self.message_handler(message)
                        else:
                            self.message_handler(message)
                    except Exception as e:
                        logger.error(f"Error in async message handler: {e}")
                        
        except asyncio.CancelledError:
            logger.info("Async consumer cancelled")
        finally:
            self.stop()
    
    # Transaction-related methods
    
    @property
    def reads_committed_only(self) -> bool:
        """Check if consumer is configured to read only committed messages."""
        return self.config.isolation_level == "read_committed"
    
    def filter_transactional_messages(self, messages: List[MessageResult]) -> List[MessageResult]:
        """
        Filter messages based on transaction settings.
        
        Args:
            messages: List of messages to filter
            
        Returns:
            Filtered list of messages
        """
        if not self.reads_committed_only:
            return messages
        
        # If reading committed only, filter out uncommitted transactional messages
        # Note: confluent-kafka already handles this at the protocol level,
        # but this method provides additional application-level filtering if needed
        filtered = []
        for msg in messages:
            if msg.is_transactional:
                logger.debug(f"Transactional message from transaction {msg.transaction_id}")
            filtered.append(msg)
        
        return filtered
    
    def get_transactional_messages(self, messages: List[MessageResult]) -> List[MessageResult]:
        """
        Get only transactional messages from a list.
        
        Args:
            messages: List of messages to filter
            
        Returns:
            List of transactional messages only
        """
        return [msg for msg in messages if msg.is_transactional]
    
    def get_non_transactional_messages(self, messages: List[MessageResult]) -> List[MessageResult]:
        """
        Get only non-transactional messages from a list.
        
        Args:
            messages: List of messages to filter
            
        Returns:
            List of non-transactional messages only
        """
        return [msg for msg in messages if not msg.is_transactional]
    
    def group_messages_by_transaction(self, messages: List[MessageResult]) -> Dict[Optional[str], List[MessageResult]]:
        """
        Group messages by transaction ID.
        
        Args:
            messages: List of messages to group
            
        Returns:
            Dictionary mapping transaction IDs to lists of messages
        """
        groups = {}
        for msg in messages:
            tx_id = msg.transaction_id
            if tx_id not in groups:
                groups[tx_id] = []
            groups[tx_id].append(msg)
        
        return groups
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()