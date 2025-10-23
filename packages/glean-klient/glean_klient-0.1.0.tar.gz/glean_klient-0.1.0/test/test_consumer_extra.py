from unittest.mock import patch, MagicMock
import pytest

from klient import KafkaConsumer, ConsumerConfig


def build_message(value: bytes, key: bytes = b'k', topic='t1', partition=0, offset=0):
    msg = MagicMock()
    msg.topic.return_value = topic
    msg.partition.return_value = partition
    msg.offset.return_value = offset
    msg.key.return_value = key
    msg.value.return_value = value
    msg.timestamp.return_value = (0, 0)
    msg.headers.return_value = []
    msg.error.return_value = None
    return msg


@patch('klient.consumer.Consumer')
def test_consume_messages_and_commit(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.consume.return_value = [build_message(b'a', offset=1), build_message(b'b', offset=2)]
    cfg = ConsumerConfig(bootstrap_servers='localhost:9092', group_id='g1')
    consumer = KafkaConsumer(cfg)
    consumer.subscribe(['t1'])
    batch = consumer.consume_messages(count=2, timeout=0.1)
    assert len(batch) == 2
    consumer.commit()
    instance.commit.assert_called()
    consumer.stop()
    assert consumer._is_running is False

@patch('klient.consumer.Consumer')
@pytest.mark.asyncio
async def test_async_consume(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.consume.return_value = [build_message(b'c', offset=3)]
    cfg = ConsumerConfig(bootstrap_servers='localhost:9092', group_id='g2')
    consumer = KafkaConsumer(cfg)
    with pytest.raises(TypeError):
        consumer.subscribe('t1')
    consumer.subscribe(['t1'])
    msgs = await consumer.aconsume_messages(count=1, timeout=0.01)
    assert len(msgs) == 1
    consumer.stop()

@patch('klient.consumer.Consumer')
@pytest.mark.asyncio
async def test_message_stream_limited(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.poll.side_effect = [build_message(b'x', offset=10), build_message(b'y', offset=11), None]
    cfg = ConsumerConfig(bootstrap_servers='localhost:9092', group_id='g3')
    consumer = KafkaConsumer(cfg)
    with pytest.raises(TypeError):
        consumer.subscribe('t1')
    consumer.subscribe(['t1'])
    consumer._is_running = True
    out = []
    async for m in consumer.amessage_stream(timeout=0.01):
        out.append(m)
        if len(out) == 2:
            consumer._is_running = False
            break
    results = out
    assert len(results) == 2
    consumer.stop()
