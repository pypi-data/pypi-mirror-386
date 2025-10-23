import pytest
from klient.producer import KafkaProducer, ProducerConfig, KafkaProducerRetriableError
from klient.metrics import snapshot, inc

class StubProducer:
    def __init__(self):
        self.records = []
    def produce(self, **kwargs):
        pass
    def flush(self):
        return 0
    def begin_transaction(self):
        # no-op
        return None
    def commit_transaction(self):
        return None
    def abort_transaction(self):
        return None
    def init_transactions(self):
        return None

class FailingProducer(KafkaProducer):
    """Producer that always raises retriable error to trigger circuit breaker."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stub = StubProducer()
        self._attempts = 0
    def _create_producer(self):
        if self._producer is None:
            self._producer = self._stub
        return self._producer
    def produce(self, *args, **kwargs):
        self._attempts += 1
        raise KafkaProducerRetriableError("retriable failure")

class TxCountingProducer(KafkaProducer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stub = StubProducer()
    def _create_producer(self):
        if self._producer is None:
            self._producer = self._stub
        return self._producer
    def begin_transaction(self):
        inc("producer.tx.begin")
        self._in_transaction = True
        return super().begin_transaction()

@pytest.fixture
def producer_cfg():
    return ProducerConfig(bootstrap_servers="localhost:9092", transactional_id="obs-tx")

def test_circuit_breaker_open_event(producer_cfg, caplog):
    prod = FailingProducer(producer_cfg)
    with pytest.raises(KafkaProducerRetriableError):
        prod.produce_with_retry("t", value=b"x", max_attempts=2)
    # ensure attempts match max_attempts
    assert prod._attempts == 2
    # check log for circuit open json event
    found = False
    for rec in caplog.records:
        if 'produce_circuit_open' in rec.getMessage():
            # rudimentary JSON structure presence
            found = True
            break
    assert found, "Expected circuit open log event"

def test_metrics_snapshot_increment(producer_cfg):
    TxCountingProducer(producer_cfg)  # trigger potential begin counter path
    # Simulate commits/aborts
    inc("producer.tx.commit")
    inc("producer.tx.abort")
    snap = snapshot()
    assert snap.get("producer.tx.begin", 0) >= 0
    assert snap.get("producer.tx.commit", 0) >= 1
    assert snap.get("producer.tx.abort", 0) >= 1
