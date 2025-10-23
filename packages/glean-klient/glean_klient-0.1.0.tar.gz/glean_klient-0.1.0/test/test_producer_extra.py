import asyncio
from unittest.mock import patch, MagicMock

from klient import KafkaProducer, ProducerConfig, ProduceResult


def collect_results():
    bucket = []
    def cb(res: ProduceResult):
        bucket.append(res)
    return bucket, cb

@patch('klient.producer.Producer')
def test_delivery_callback_invoked(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    # Simulate produce with callback execution
    def produce_side_effect(*args, **kwargs):
        delivery_cb = kwargs.get('callback') or kwargs.get('on_delivery')
        if delivery_cb:
            # Fake success message object
            msg = MagicMock()
            msg.topic.return_value = 'demo'
            msg.partition.return_value = 0
            msg.offset.return_value = 42
            delivery_cb(None, msg)
    instance.produce.side_effect = produce_side_effect
    instance.flush.return_value = 0

    bucket, cb = collect_results()
    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092'), delivery_callback=cb)
    producer.produce('demo', value='hello', key='k1', headers={'x':'y'})
    producer.flush()
    assert len(bucket) == 1
    assert bucket[0].success is True
    assert bucket[0].topic == 'demo'

@patch('klient.producer.Producer')
def test_custom_callback(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    def produce_side_effect(*args, **kwargs):
        delivery_cb = kwargs.get('callback') or kwargs.get('on_delivery')
        if delivery_cb:
            msg = MagicMock()
            msg.topic.return_value = 'custom'
            msg.partition.return_value = 1
            msg.offset.return_value = 7
            delivery_cb(None, msg)
    instance.produce.side_effect = produce_side_effect

    bucket, cb = collect_results()
    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092'))
    producer.produce('custom', value=b'data', callback=cb)
    assert len(bucket) == 1
    assert bucket[0].partition == 1

@patch('klient.producer.Producer')
def test_close_flush(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.flush.return_value = 0
    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092'))
    producer.flush()
    producer.close()
    instance.flush.assert_called()

@patch('klient.producer.Producer')
def test_aproduce_async(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance

    async def runner():
        producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092'))
        await producer.aproduce('a', value='async-msg')
        await producer.aflush()
        producer.close()
    asyncio.run(runner())
    instance.produce.assert_called()
    instance.flush.assert_called()
