import pytest
from klient.producer import KafkaProducer, ProducerConfig, KafkaProducerRetriableError

class StubProducer:
    def __init__(self):
        self.records = []
    def produce(self, **kwargs):
        # mimic confluent producer interface; unused in stub path
        pass
    def flush(self):
        return 0

class DummyProducer(KafkaProducer):
    def __init__(self, *args, fail_times=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._fail_times = fail_times
        self._attempts = 0
        self._stub = StubProducer()
    def _create_producer(self):  # override to avoid real broker
        if self._producer is None:
            self._producer = self._stub
        return self._producer
    def produce(self, *args, **kwargs):  # simulate retry errors then success (no real produce)
        self._attempts += 1
        if self._attempts <= self._fail_times:
            raise KafkaProducerRetriableError("temporary")
        # success: do nothing
        return None

@pytest.fixture
def producer_cfg():
    return ProducerConfig(bootstrap_servers="localhost:9092")

def test_retry_succeeds_after_transient_errors(producer_cfg):
    prod = DummyProducer(producer_cfg, fail_times=2)
    prod.produce_with_retry("t", value=b"x", max_attempts=5)
    assert prod._attempts == 3

def test_retry_exhaustion(producer_cfg):
    prod = DummyProducer(producer_cfg, fail_times=10)
    with pytest.raises(KafkaProducerRetriableError):
        prod.produce_with_retry("t", value=b"x", max_attempts=3)
    assert prod._attempts == 3
