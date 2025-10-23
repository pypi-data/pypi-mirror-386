import pytest
from klient.consumer import KafkaConsumer, ConsumerConfig, KafkaConsumerRebalanceError

class DummyPartition:
    def __init__(self, partition):
        self.partition = partition

class DummyConsumer:
    pass

@pytest.fixture
def config():
    return ConsumerConfig(bootstrap_servers="localhost:9092", group_id="g")

def test_on_assign_success(monkeypatch, config):
    assigned = []
    def on_assign(consumer, parts):
        assigned.extend(p.partition for p in parts)
    kc = KafkaConsumer(config, on_assign=on_assign)
    # Invoke wrapper directly
    wrapper = kc._wrap_on_assign(on_assign)
    assert wrapper is not None
    wrapper(DummyConsumer(), [DummyPartition(1), DummyPartition(2)])
    assert assigned == [1,2]

def test_on_revoke_error(monkeypatch, config):
    def on_revoke(_c, _p):
        raise RuntimeError("boom")
    kc = KafkaConsumer(config, on_revoke=on_revoke)
    wrapper = kc._wrap_on_revoke(on_revoke)
    assert wrapper is not None
    with pytest.raises(KafkaConsumerRebalanceError):
        wrapper(DummyConsumer(), [DummyPartition(3)])

def test_on_lost(monkeypatch, config):
    lost = []
    def on_lost(_c, parts):
        lost.extend(p.partition for p in parts)
    kc = KafkaConsumer(config, on_lost=on_lost)
    wrapper = kc._wrap_on_lost(on_lost)
    assert wrapper is not None
    wrapper(DummyConsumer(), [DummyPartition(9)])
    assert lost == [9]
