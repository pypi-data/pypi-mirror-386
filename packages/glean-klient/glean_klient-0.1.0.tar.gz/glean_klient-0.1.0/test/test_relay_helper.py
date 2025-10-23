import pytest
from klient.relay import ExactlyOnceRelay
from klient.consumer import KafkaConsumer, ConsumerConfig, MessageResult
from klient.producer import KafkaProducer, ProducerConfig, KafkaTransactionError

class DummyConsumer(KafkaConsumer):
    def __init__(self, config, batches):
        super().__init__(config)
        self._batches = batches
        self._consumed = 0
    def subscribe(self, topics):
        assert isinstance(topics, list)
    def consume_messages(self, count=1, timeout=1.0):
        if self._consumed >= len(self._batches):
            return []
        batch = self._batches[self._consumed]
        self._consumed += 1
        return batch
    async def aconsume_messages(self, count=1, timeout=1.0):
        return self.consume_messages(count, timeout)
    def commit(self, message=None):
        pass

class DummyProducer(KafkaProducer):
    def __init__(self, config):
        # avoid real init; do not call super that triggers _create_producer early
        self.config = config
        self.delivery_callback = None
        self._producer = None
        self._executor = None
        self._in_transaction = False
        self._transaction_id = config.transactional_id
        self._produced = []
    def _create_producer(self):
        # stub object
        if self._producer is None:
            class Stub:
                def flush(self):
                    return 0
            self._producer = Stub()
        return self._producer
    def produce(self, topic, value=None, key=None, headers=None, partition=None, callback=None, flush=False):
        self._produced.append((topic, key, value))
    async def aproduce(self, topic, value=None, key=None, headers=None, partition=None, callback=None, flush=False):
        self.produce(topic, value=value, key=key, headers=headers, partition=partition, callback=callback, flush=flush)
    def begin_transaction(self):
        from klient.producer import TransactionResult
        if self._in_transaction:
            raise KafkaTransactionError("already in tx")
        self._in_transaction = True
        return TransactionResult(transaction_id=self._transaction_id or '', success=True, operation="begin")
    def commit_transaction(self):
        from klient.producer import TransactionResult
        if not self._in_transaction:
            raise KafkaTransactionError("no tx")
        self._in_transaction = False
        return TransactionResult(transaction_id=self._transaction_id or '', success=True, operation="commit")
    def abort_transaction(self):
        from klient.producer import TransactionResult
        self._in_transaction = False
        return TransactionResult(transaction_id=self._transaction_id or '', success=True, operation="abort")

@pytest.fixture
def msg():
    return MessageResult(topic="in", partition=0, offset=0, key=b"k", value=b"v", timestamp=(0,0))

@pytest.fixture
def relay_instances(msg):
    batches = [[msg], [msg]]
    cons = DummyConsumer(ConsumerConfig(bootstrap_servers="localhost:9092", group_id="g"), batches)
    prod = DummyProducer(ProducerConfig(bootstrap_servers="localhost:9092", transactional_id="tx"))
    return cons, prod

def test_sync_relay(relay_instances):
    cons, prod = relay_instances
    relay = ExactlyOnceRelay(cons, prod, batch_size=1)
    relay.run("in", "out", stop_on_empty=True)
    assert len(prod._produced) >= 2

def test_requires_transactional_producer(msg):
    cons = DummyConsumer(ConsumerConfig(bootstrap_servers="localhost:9092", group_id="g"), [[msg]])
    non_tx_prod = KafkaProducer(ProducerConfig(bootstrap_servers="localhost:9092"))
    with pytest.raises(ValueError):
        ExactlyOnceRelay(cons, non_tx_prod)
