import asyncio
import pytest

from klient.consumer import ConsumerConfig
from klient.producer import ProducerConfig, KafkaTransactionError, KafkaProducerRetriableError

# Dummy message result for simulation
from klient.consumer import MessageResult

class DummyMessage(MessageResult):
    pass

class LoopingConsumer:
    """Simulates streaming consumption producing a finite number of messages."""
    def __init__(self, total: int):
        self._remaining = total
        self._is_running = True
        self.config = ConsumerConfig(bootstrap_servers="localhost:9092", group_id="relay-test")
    def subscribe(self, topics):
        assert isinstance(topics, list)
    def message_stream(self, timeout=0.1):
        while self._remaining > 0:
            self._remaining -= 1
            yield MessageResult(topic="in", partition=0, offset=self._remaining, key=b"k", value=b"v", timestamp=(0,0))
    async def amessage_stream(self, timeout=0.1):
        while self._remaining > 0:
            self._remaining -= 1
            yield MessageResult(topic="in", partition=0, offset=self._remaining, key=b"k", value=b"v", timestamp=(0,0))
    def commit(self):
        pass
    def stop(self):
        self._is_running = False

class DummyProducer:
    def __init__(self, transactional_id="tx", fail_attempts=0):
        self.config = ProducerConfig(bootstrap_servers="localhost:9092", transactional_id=transactional_id)
        self._in_tx = False
        self._produced = []
        self._attempt_counter = 0
        self._fail_attempts = fail_attempts
    def begin_transaction(self):
        from klient.producer import TransactionResult
        if self._in_tx:
            raise KafkaTransactionError("already in transaction")
        self._in_tx = True
        return TransactionResult(transaction_id=self.config.transactional_id or '', success=True, operation="begin")
    def commit_transaction(self):
        from klient.producer import TransactionResult
        if not self._in_tx:
            raise KafkaTransactionError("no active transaction")
        self._in_tx = False
        return TransactionResult(transaction_id=self.config.transactional_id or '', success=True, operation="commit")
    def abort_transaction(self):
        from klient.producer import TransactionResult
        self._in_tx = False
        return TransactionResult(transaction_id=self.config.transactional_id or '', success=True, operation="abort")
    def produce(self, topic, key=None, value=None, **kwargs):
        self._attempt_counter += 1
        if self._fail_attempts > 0:
            self._fail_attempts -= 1
            raise KafkaProducerRetriableError("transient produce failure")
        self._produced.append((topic, key, value))
    async def aproduce(self, topic, key=None, value=None, **kwargs):
        return self.produce(topic, key=key, value=value, **kwargs)
    async def aproduce_with_retry(self, *args, **kwargs):
        # Simplified retry that mirrors wrapper signature for test; call plain aproduce
        attempts = kwargs.pop("max_attempts", 3)
        for i in range(attempts):
            try:
                return await self.aproduce(*args, **kwargs)
            except KafkaProducerRetriableError:
                if i == attempts - 1:
                    raise
                await asyncio.sleep(0)
    @property
    def in_transaction(self):
        return self._in_tx
    def close(self):
        pass

@pytest.mark.parametrize("batch_size,total", [(5, 12)])
def test_sync_continuous_relay(batch_size, total):
    cons = LoopingConsumer(total)
    cons.subscribe(["in"])
    prod = DummyProducer(transactional_id="sync-tx")
    buffer = []
    commits = 0
    for msg in cons.message_stream():
        buffer.append(msg)
        if len(buffer) >= batch_size:
            prod.begin_transaction()
            for m in buffer:
                prod.produce("out", key=m.key.decode() if m.key else None, value=m.value)
            prod.commit_transaction()
            cons.commit()
            buffer.clear()
            commits += 1
    # Drain remainder
    if buffer:
        prod.begin_transaction()
        for m in buffer:
            prod.produce("out", key=m.key.decode() if m.key else None, value=m.value)
        prod.commit_transaction()
        cons.commit()
        commits += 1
    assert commits >= 1
    assert len(prod._produced) == total

@pytest.mark.asyncio
async def test_async_continuous_relay_with_retry():
    cons = LoopingConsumer(15)
    cons.subscribe(["in"])
    # Fail first 3 attempts across produces to exercise retry logic
    prod = DummyProducer(transactional_id="async-tx", fail_attempts=3)
    buffer = []
    batch_size = 7
    commits = 0
    async for msg in cons.amessage_stream():
        buffer.append(msg)
        if len(buffer) >= batch_size:
            prod.begin_transaction()
            for m in buffer:
                # Use simplified retry wrapper; expects eventual success after transient failures
                await prod.aproduce_with_retry("out", key=m.key.decode() if m.key else None, value=m.value, max_attempts=4)
            prod.commit_transaction()
            cons.commit()
            buffer.clear()
            commits += 1
    if buffer:
        prod.begin_transaction()
        for m in buffer:
            await prod.aproduce_with_retry("out", key=m.key.decode() if m.key else None, value=m.value, max_attempts=4)
        prod.commit_transaction()
        cons.commit()
        commits += 1
    assert commits >= 1
    assert len(prod._produced) == 15
    # Ensure retry attempts happened (attempt counter > produced messages)
    assert prod._attempt_counter > len(prod._produced)
