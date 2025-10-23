import pytest
from klient.producer import KafkaProducer, ProducerConfig, KafkaProducerRetriableError

class AsyncStubProducer:
    def produce(self, **kwargs):
        pass
    def flush(self):
        return 0

class DummyAsyncRetriable(KafkaProducer):
    def __init__(self, *args, fail_times=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._fail_times = fail_times
        self._attempts = 0
        self._stub = AsyncStubProducer()
    def _create_producer(self):
        if self._producer is None:
            self._producer = self._stub
        return self._producer
    def produce(self, *args, **kwargs):
        self._attempts += 1
        if self._attempts <= self._fail_times:
            raise KafkaProducerRetriableError("temp")
        return None

@pytest.mark.asyncio
async def test_async_retry_success():
    prod = DummyAsyncRetriable(ProducerConfig(bootstrap_servers="localhost:9092"), fail_times=2)
    await prod.aproduce_with_retry("t", value=b"x", max_attempts=5)
    assert prod._attempts == 3

@pytest.mark.asyncio
async def test_async_retry_exhaustion():
    prod = DummyAsyncRetriable(ProducerConfig(bootstrap_servers="localhost:9092"), fail_times=5)
    with pytest.raises(KafkaProducerRetriableError):
        await prod.aproduce_with_retry("t", value=b"x", max_attempts=3)
    assert prod._attempts == 3
