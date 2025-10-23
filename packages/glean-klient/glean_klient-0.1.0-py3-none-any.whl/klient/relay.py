"""High-level exactly-once style relay helper.

Consumes messages from a source topic and produces them transactionally to a target topic.
Offsets are committed only after the transaction successfully commits, approximating exactly-once
semantics when using Kafka transactions + read_committed consumers.

Note: Full EOS guarantees require proper isolation level and broker support. This helper focuses on
application-level sequencing and commit discipline.
"""

from typing import Callable, Optional, List
import asyncio
import logging

from .consumer import KafkaConsumer, MessageResult
from .producer import KafkaProducer

logger = logging.getLogger(__name__)


class ExactlyOnceRelay:
    def __init__(
        self,
        source_consumer: KafkaConsumer,
        target_producer: KafkaProducer,
        transform: Optional[Callable[[MessageResult], MessageResult]] = None,
        batch_size: int = 50,
        poll_timeout: float = 1.0,
    ):
        if not target_producer.supports_transactions:
            raise ValueError("target_producer must be transactional for exactly-once relay")
        self.source_consumer = source_consumer
        self.target_producer = target_producer
        self.transform = transform
        self.batch_size = batch_size
        self.poll_timeout = poll_timeout
        self._running = False

    def _prepare_batch(self) -> List[MessageResult]:
        msgs = self.source_consumer.consume_messages(count=self.batch_size, timeout=self.poll_timeout)
        return msgs

    def run(self, source_topic: str, target_topic: str, stop_on_empty: bool = False):
        """Run relay synchronously.

        Args:
            source_topic: topic to consume
            target_topic: topic to produce
            stop_on_empty: if True, exit loop when a poll returns no messages
        """
        self.source_consumer.subscribe([source_topic])
        self._running = True
        while self._running:
            batch = self._prepare_batch()
            if not batch:
                if stop_on_empty:
                    break
                continue
            with self.target_producer.transaction():
                for msg in batch:
                    out = self.transform(msg) if self.transform else msg
                    self.target_producer.produce(target_topic, key=out.key, value=out.value)
            # Commit offsets after successful transaction
            self.source_consumer.commit()

    async def arun(self, source_topic: str, target_topic: str, stop_on_empty: bool = False, max_in_flight: int = 1):
        """Run relay asynchronously.

        Args:
            source_topic: topic to consume
            target_topic: topic to produce
            stop_on_empty: if True, exit loop when a poll returns no messages
        """
        self.source_consumer.subscribe([source_topic])
        self._running = True
        semaphore = asyncio.Semaphore(max_in_flight)
        async def process_batch(batch):
            async with semaphore:
                async with self.target_producer.atransaction():
                    for msg in batch:
                        out = self.transform(msg) if self.transform else msg
                        await self.target_producer.aproduce(target_topic, key=out.key, value=out.value)
                self.source_consumer.commit()

        tasks = []
        while self._running:
            batch = await self.source_consumer.aconsume_messages(count=self.batch_size, timeout=self.poll_timeout)
            if not batch:
                if stop_on_empty:
                    break
                await asyncio.sleep(0.05)
                continue
            tasks.append(asyncio.create_task(process_batch(batch)))
        # finalize
        for t in tasks:
            await t

    def stop(self):
        self._running = False
        self.source_consumer.stop()
        self.target_producer.close()
