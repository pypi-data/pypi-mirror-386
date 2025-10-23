"""
Kafka producer wrapper that supports both synchronous and asynchronous operations.
"""

import asyncio
import logging
from typing import Dict, Optional, Union, Callable, Any, List
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from confluent_kafka import Producer, KafkaError
import json
from .metrics import inc
from . import resolve_env_config, split_env_config, extract_bootstrap


logger = logging.getLogger(__name__)

# Kafka error code buckets (extend as needed). Using integer values avoids attribute reliance.
# Source: confluent_kafka.error.KafkaError error codes. Not exhaustive; focused on common operational cases.
# Retriable examples: _TRANSPORT, _MSG_TIMED_OUT, _ALL_BROKERS_DOWN (transient), _TIMED_OUT, _QUEUE_FULL
# Fatal examples: _INVALID_ARG, _UNKNOWN_PARTITION, _UNKNOWN_TOPIC
# Fencing: ERR__FENCED (when transactional.id is claimed by another producer instance)
try:
    RETRIABLE_ERROR_CODES = {
        KafkaError._TRANSPORT,
        KafkaError._MSG_TIMED_OUT,
        KafkaError._ALL_BROKERS_DOWN,
        KafkaError._TIMED_OUT,
        KafkaError._QUEUE_FULL,
    }
    FATAL_ERROR_CODES = {
        KafkaError._INVALID_ARG,
        KafkaError._UNKNOWN_PARTITION,
        KafkaError._UNKNOWN_TOPIC,
    }
    # Fencing error constant may differ across versions; guard existence
    FENCING_ERROR_CODES = {getattr(KafkaError, '_FENCED', -9999)}
except AttributeError:
    # Fallback if constants not present in version; keep sets empty to avoid misclassification
    RETRIABLE_ERROR_CODES = set()
    FATAL_ERROR_CODES = set()
    FENCING_ERROR_CODES = set()


@dataclass
class ProducerConfig:
    """Configuration for Kafka producer."""
    bootstrap_servers: str
    acks: str = "all"
    retries: int = 3
    batch_size: int = 16384
    linger_ms: int = 0
    compression_type: str = "none"
    max_in_flight_requests_per_connection: int = 5
    enable_idempotence: bool = True
    # Transaction settings
    transactional_id: Optional[str] = None
    transaction_timeout_ms: int = 60000
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_confluent_config(self) -> Dict[str, Any]:
        """Convert to confluent-kafka configuration format."""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'acks': self.acks,
            'retries': self.retries,
            'batch.size': self.batch_size,
            'linger.ms': self.linger_ms,
            'compression.type': self.compression_type,
            'max.in.flight.requests.per.connection': self.max_in_flight_requests_per_connection,
            'enable.idempotence': self.enable_idempotence,
        }
        
        # Add transaction config if enabled
        if self.transactional_id:
            config['transactional.id'] = self.transactional_id
            config['transaction.timeout.ms'] = self.transaction_timeout_ms
            # Force settings required for transactions
            config['enable.idempotence'] = True
            config['acks'] = 'all'
            config['retries'] = 2147483647  # Max value
            config['max.in.flight.requests.per.connection'] = 5
        
        config.update(self.additional_config)
        return config


@dataclass
class ProduceResult:
    """Result of a produce operation."""
    topic: str
    partition: int
    offset: int
    success: bool
    error: Optional[str] = None


@dataclass
class TransactionResult:
    """Result of a transaction operation."""
    transaction_id: str
    success: bool
    operation: str  # 'begin', 'commit', 'abort'
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class KafkaProducerError(Exception):
    """Custom exception for Kafka producer errors."""
    pass


class KafkaTransactionError(KafkaProducerError):
    """Custom exception for Kafka transaction errors."""
    pass

class KafkaProducerRetriableError(KafkaProducerError):
    """Retriable produce or transaction error."""
    pass

class KafkaProducerFatalError(KafkaProducerError):
    """Fatal non-retriable error."""
    pass

class KafkaProducerFencedError(KafkaTransactionError):
    """Transaction fenced (e.g., another producer with same transactional.id started)."""
    pass


class KafkaProducer:
    """
    Kafka producer wrapper that supports both sync and async operations with transaction support.
    """
    
    def __init__(self, config: ProducerConfig, delivery_callback: Optional[Callable[[ProduceResult], None]] = None):
        """
        Initialize Kafka producer.
        
        Args:
            config: Producer configuration
            delivery_callback: Optional callback for delivery reports
        """
        self.config = config
        self.delivery_callback = delivery_callback
        self._producer = None
        self._executor = None
        self._in_transaction = False
        self._transaction_id = config.transactional_id

    @classmethod
    def from_env_config(
        cls,
        env: Optional[str] = None,
        config_file: Optional[str] = None,
        transactional_id: Optional[str] = None,
        delivery_callback: Optional[Callable[[ProduceResult], None]] = None,
    ) -> 'KafkaProducer':
        """Construct a KafkaProducer using environment configuration files.

        Args:
            env: Environment name to resolve (e.g. 'sit').
            config_file: Explicit path to config JSON (optional).
            transactional_id: Override transactional id; if None will use one from config.
            delivery_callback: Optional delivery callback.
        """
        raw = resolve_env_config(env, config_file)
        prod_raw, _, _ = split_env_config(raw)
        effective_bootstrap = extract_bootstrap([prod_raw]) or 'localhost:9092'
        # allow config to supply transactional.id
        if not transactional_id and 'transactional.id' in prod_raw:
            transactional_id = prod_raw['transactional.id']
        addl = dict(prod_raw)
        for k in ['bootstrap.servers', 'transactional.id']:
            addl.pop(k, None)
        cfg = ProducerConfig(
            bootstrap_servers=effective_bootstrap,
            transactional_id=transactional_id,
            additional_config=addl,
        )
        return cls(cfg, delivery_callback)
        
    def _create_producer(self) -> Producer:
        """Create and return a new Producer instance."""
        if self._producer is None:
            try:
                self._producer = Producer(self.config.to_confluent_config())
                logger.info("Created Kafka producer")
                
                # Initialize transactions if transactional_id is set
                if self._transaction_id:
                    self._init_transactions()
                    
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise KafkaProducerError(f"Failed to create producer: {e}")
        return self._producer
    
    def _init_transactions(self) -> None:
        """Initialize transactions for the producer."""
        try:
            producer = self._create_producer()
            producer.init_transactions()
            logger.info(f"Initialized transactions for producer with ID: {self._transaction_id}")
        except Exception as e:
            logger.error(f"Failed to initialize transactions: {e}")
            raise KafkaTransactionError(f"Transaction initialization failed: {e}")
    
    @property
    def supports_transactions(self) -> bool:
        """Check if this producer supports transactions."""
        return self._transaction_id is not None
    
    @property
    def in_transaction(self) -> bool:
        """Check if producer is currently in a transaction."""
        return self._in_transaction
    
    def _delivery_report(self, err, msg):
        """Internal delivery report callback."""
        if err is not None:
            result = ProduceResult(
                topic=msg.topic() if msg else "unknown",
                partition=-1,
                offset=-1,
                success=False,
                error=str(err)
            )
            if isinstance(err, KafkaError):
                code = getattr(err, 'code', lambda: None)()
                if code in FENCING_ERROR_CODES:
                    logger.error(f"Fencing delivery error (code={code}): {err}")
                elif code in RETRIABLE_ERROR_CODES:
                    logger.warning(f"Retriable delivery error (code={code}): {err}")
                elif code in FATAL_ERROR_CODES:
                    logger.critical(f"Fatal delivery error (code={code}): {err}")
                else:
                    logger.error(f"Delivery error (code={code}): {err}")
            else:
                logger.error(f"Message delivery failed: {err}")
        else:
            result = ProduceResult(
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
                success=True
            )
            logger.debug(f"Message delivered to {msg.topic()}[{msg.partition()}] at offset {msg.offset()}")
        
        if self.delivery_callback:
            try:
                self.delivery_callback(result)
            except Exception as e:
                logger.error(f"Error in delivery callback: {e}")
    
    def produce(
        self, 
        topic: str, 
        value: Optional[Union[str, bytes]] = None,
        key: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, Union[str, bytes]]] = None,
        partition: Optional[int] = None,
        callback: Optional[Callable[[ProduceResult], None]] = None,
        flush: bool = False
    ) -> None:
        """
        Produce a message synchronously.
        
        Args:
            topic: Topic to produce to
            value: Message value
            key: Message key
            headers: Message headers
            partition: Specific partition (optional)
            callback: Per-message callback (optional)
            flush: Whether to flush immediately
        """
        producer = self._create_producer()
        
        # Convert string values to bytes if needed
        if isinstance(value, str):
            value = value.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        # Convert headers to bytes if needed
        if headers:
            headers = {k: v.encode('utf-8') if isinstance(v, str) else v for k, v in headers.items()}
        
        try:
            # Use custom callback if provided, otherwise use instance callback
            delivery_cb = None
            if callback:
                def custom_delivery_report(err, msg):
                    if err is not None:
                        result = ProduceResult(
                            topic=msg.topic() if msg else topic,
                            partition=-1,
                            offset=-1,
                            success=False,
                            error=str(err)
                        )
                    else:
                        result = ProduceResult(
                            topic=msg.topic(),
                            partition=msg.partition(),
                            offset=msg.offset(),
                            success=True
                        )
                    callback(result)
                delivery_cb = custom_delivery_report
            else:
                delivery_cb = self._delivery_report
            
            producer.produce(
                topic=topic,
                value=value,
                key=key,
                headers=headers,
                partition=partition,
                callback=delivery_cb
            )
            
            if flush:
                producer.flush()
                
        except Exception as e:
            logger.error(f"Error producing message: {e}")
            raise KafkaProducerError(f"Produce error: {e}")
    
    def produce_batch(
        self, 
        messages: List[Dict[str, Any]], 
        flush: bool = True
    ) -> None:
        """
        Produce multiple messages in a batch.
        
        Args:
            messages: List of message dictionaries with keys: topic, value, key, headers, partition
            flush: Whether to flush after producing all messages
        """
        producer = self._create_producer()
        
        for msg_dict in messages:
            try:
                self.produce(
                    topic=msg_dict['topic'],
                    value=msg_dict.get('value'),
                    key=msg_dict.get('key'),
                    headers=msg_dict.get('headers'),
                    partition=msg_dict.get('partition'),
                    callback=msg_dict.get('callback'),
                    flush=False  # Don't flush individual messages
                )
            except Exception as e:
                logger.error(f"Error producing message in batch: {e}")
                raise
        
        if flush:
            producer.flush()
    
    async def aproduce(
        self, 
        topic: str, 
        value: Optional[Union[str, bytes]] = None,
        key: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, Union[str, bytes]]] = None,
        partition: Optional[int] = None,
        callback: Optional[Callable[[ProduceResult], None]] = None,
        flush: bool = False
    ) -> None:
        """
        Produce a message asynchronously.
        
        Args:
            topic: Topic to produce to
            value: Message value
            key: Message key
            headers: Message headers
            partition: Specific partition (optional)
            callback: Per-message callback (optional)
            flush: Whether to flush immediately
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor, 
            self.produce, 
            topic, value, key, headers, partition, callback, flush
        )
    
    async def aproduce_batch(
        self, 
        messages: List[Dict[str, Any]], 
        flush: bool = True
    ) -> None:
        """
        Produce multiple messages asynchronously.
        
        Args:
            messages: List of message dictionaries
            flush: Whether to flush after producing all messages
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self.produce_batch, messages, flush)
    
    def flush(self, timeout: float = -1) -> int:
        """
        Flush pending messages.
        
        Args:
            timeout: Timeout in seconds (-1 for infinite)
            
        Returns:
            Number of messages still in queue
        """
        producer = self._create_producer()
        
        try:
            return producer.flush(timeout)
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")
            raise KafkaProducerError(f"Flush error: {e}")
    
    async def aflush(self, timeout: float = -1) -> int:
        """
        Flush pending messages asynchronously.
        
        Args:
            timeout: Timeout in seconds (-1 for infinite)
            
        Returns:
            Number of messages still in queue
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.flush, timeout)
    
    def poll(self, timeout: float = 0) -> int:
        """
        Poll for delivery report callbacks.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Number of events processed
        """
        producer = self._create_producer()
        
        try:
            return producer.poll(timeout)
        except Exception as e:
            logger.error(f"Error polling producer: {e}")
            raise KafkaProducerError(f"Poll error: {e}")

    # Retry Logic
    def produce_with_retry(self, *args, max_attempts: int = 5, base_backoff: float = 0.05, **kwargs) -> None:
        """Produce with simple exponential backoff on retriable errors.

        Args:
            *args/**kwargs: forwarded to produce()
            max_attempts: maximum attempts including first try
            base_backoff: initial sleep seconds; doubled each retry
        Raises:
            KafkaProducerFatalError on fatal error
            KafkaProducerError if retries exhausted
        """
        attempt = 0
        consecutive_failures = 0
        circuit_open = False
        while True:
            try:
                self.produce(*args, **kwargs)
                if circuit_open:
                    logger.info("Circuit closed after successful produce")
                return
            except KafkaProducerRetriableError as re:
                attempt += 1
                consecutive_failures += 1
                if attempt >= max_attempts:
                    circuit_open = True
                    logger.error(json.dumps({"event":"produce_circuit_open","attempts":attempt,"error":str(re)}))
                    raise
                import random
                sleep_time = base_backoff * (2 ** (attempt - 1))
                # jitter +/-10%
                jitter = sleep_time * 0.1 * (random.random() - 0.5)
                sleep_time = max(0.0, sleep_time + jitter)
                logger.warning(f"Retriable produce error (attempt {attempt}/{max_attempts}), sleeping {sleep_time:.3f}s: {re}")
                import time
                time.sleep(sleep_time)
            except KafkaProducerFatalError:
                raise
            except KafkaProducerError:
                # Non-retriable generic error
                raise

    async def aproduce_with_retry(self, *args, max_attempts: int = 5, base_backoff: float = 0.05, **kwargs) -> None:
        """Async counterpart of produce_with_retry using asyncio.sleep."""
        attempt = 0
        consecutive_failures = 0
        circuit_open = False
        while True:
            try:
                await self.aproduce(*args, **kwargs)
                if circuit_open:
                    logger.info("Async circuit closed after successful produce")
                return
            except KafkaProducerRetriableError as re:
                attempt += 1
                consecutive_failures += 1
                if attempt >= max_attempts:
                    circuit_open = True
                    logger.error(json.dumps({"event":"produce_async_circuit_open","attempts":attempt,"error":str(re)}))
                    raise
                import random
                sleep_time = base_backoff * (2 ** (attempt - 1))
                jitter = sleep_time * 0.1 * (random.random() - 0.5)
                sleep_time = max(0.0, sleep_time + jitter)
                logger.warning(f"Retriable async produce error (attempt {attempt}/{max_attempts}), sleeping {sleep_time:.3f}s: {re}")
                await asyncio.sleep(sleep_time)
            except KafkaProducerFatalError:
                raise
            except KafkaProducerError:
                raise
    
    # Transaction Methods
    
    def begin_transaction(self) -> TransactionResult:
        """
        Begin a new transaction.
        
        Returns:
            TransactionResult with operation details
        """
        if not self.supports_transactions:
            raise KafkaTransactionError("Producer not configured for transactions")
        
        if self._in_transaction:
            raise KafkaTransactionError("Transaction already in progress")
        
        producer = self._create_producer()
        
        try:
            import time
            start_time = time.time()
            
            producer.begin_transaction()
            self._in_transaction = True
            inc("producer.tx.begin")
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=True,
                operation="begin",
                duration_ms=duration_ms
            )
            
            logger.info(json.dumps({"event":"transaction_begin","transaction_id":self._transaction_id,"duration_ms":duration_ms}))
            return result
            
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=False,
                operation="begin",
                error=str(e)
            )
            # Fenced detection
            if isinstance(e, KafkaError):
                # Placeholder: extend with explicit error code mapping if needed
                raise KafkaTransactionError(f"Begin transaction failed (KafkaError): {e}")
            raise KafkaTransactionError(f"Begin transaction failed: {e}")
    
    def commit_transaction(self) -> TransactionResult:
        """
        Commit the current transaction.
        
        Returns:
            TransactionResult with operation details
        """
        if not self.supports_transactions:
            raise KafkaTransactionError("Producer not configured for transactions")
        
        if not self._in_transaction:
            raise KafkaTransactionError("No active transaction to commit")
        
        producer = self._create_producer()
        
        try:
            import time
            start_time = time.time()
            
            producer.commit_transaction()
            self._in_transaction = False
            inc("producer.tx.commit")
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=True,
                operation="commit",
                duration_ms=duration_ms
            )
            
            logger.info(json.dumps({"event":"transaction_commit","transaction_id":self._transaction_id,"duration_ms":duration_ms}))
            return result
            
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            self._in_transaction = False  # Reset state even on failure
            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=False,
                operation="commit",
                error=str(e)
            )
            if isinstance(e, KafkaError):
                raise KafkaTransactionError(f"Commit transaction failed (KafkaError): {e}")
            raise KafkaTransactionError(f"Commit transaction failed: {e}")
    
    def abort_transaction(self) -> TransactionResult:
        """
        Abort the current transaction.
        
        Returns:
            TransactionResult with operation details
        """
        if not self.supports_transactions:
            raise KafkaTransactionError("Producer not configured for transactions")
        
        if not self._in_transaction:
            raise KafkaTransactionError("No active transaction to abort")
        
        producer = self._create_producer()
        
        try:
            import time
            start_time = time.time()

            producer.abort_transaction()
            self._in_transaction = False
            inc("producer.tx.abort")

            duration_ms = (time.time() - start_time) * 1000

            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=True,
                operation="abort",
                duration_ms=duration_ms
            )

            logger.info(json.dumps({"event":"transaction_abort","transaction_id":self._transaction_id,"duration_ms":duration_ms}))
            return result

        except Exception as e:
            logger.error(f"Failed to abort transaction: {e}")
            self._in_transaction = False  # Reset state even on failure
            result = TransactionResult(
                transaction_id=self._transaction_id or '',
                success=False,
                operation="abort",
                error=str(e)
            )
            if isinstance(e, KafkaError):
                raise KafkaTransactionError(f"Abort transaction failed (KafkaError): {e}")
            raise KafkaTransactionError(f"Abort transaction failed: {e}")
    
    # Async Transaction Methods
    
    async def abegin_transaction(self) -> TransactionResult:
        """
        Begin a new transaction asynchronously.
        
        Returns:
            TransactionResult with operation details
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.begin_transaction)
    
    async def acommit_transaction(self) -> TransactionResult:
        """
        Commit the current transaction asynchronously.
        
        Returns:
            TransactionResult with operation details
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.commit_transaction)
    
    async def aabort_transaction(self) -> TransactionResult:
        """
        Abort the current transaction asynchronously.
        
        Returns:
            TransactionResult with operation details
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.abort_transaction)
    
    # Transaction Context Manager
    
    class TransactionContext:
        """Context manager for transactions."""
        
        def __init__(self, producer: 'KafkaProducer'):
            self.producer = producer
            self.result = None
        
        def __enter__(self):
            self.result = self.producer.begin_transaction()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                # Exception occurred, abort transaction
                try:
                    self.producer.abort_transaction()
                except Exception as e:
                    logger.error(f"Failed to abort transaction during exception handling: {e}")
            else:
                # Success, commit transaction
                self.producer.commit_transaction()
    
    class AsyncTransactionContext:
        """Async context manager for transactions."""
        def __init__(self, producer: 'KafkaProducer'):
            self.producer = producer
            self.result = None
        
        async def __aenter__(self):
            self.result = await self.producer.abegin_transaction()
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                try:
                    await self.producer.aabort_transaction()
                except Exception as e:
                    logger.error(f"Failed to abort transaction during exception handling: {e}")
            else:
                await self.producer.acommit_transaction()
    
    def transaction(self) -> 'KafkaProducer.TransactionContext':
        """
        Create a transaction context manager.
        
        Usage:
            with producer.transaction():
                producer.produce(...)
                producer.produce(...)
                # Auto-commit on success, auto-abort on exception
        """
        return self.TransactionContext(self)
    
    def atransaction(self) -> 'KafkaProducer.AsyncTransactionContext':
        """
        Create an async transaction context manager.
        
        Usage:
            async with producer.atransaction():
                await producer.aproduce(...)
                await producer.aproduce(...)
                # Auto-commit on success, auto-abort on exception
        """
        return self.AsyncTransactionContext(self)
    
    def close(self) -> None:
        """Close the producer and clean up resources."""
        # Abort any active transaction before closing
        if self._in_transaction:
            try:
                logger.warning("Aborting active transaction during producer close")
                self.abort_transaction()
            except Exception as e:
                logger.error(f"Failed to abort transaction during close: {e}")
        
        if self._producer:
            try:
                # Flush any remaining messages
                self._producer.flush()
                logger.info("Producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
            finally:
                self._producer = None
                
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()