import pytest
from unittest.mock import patch, MagicMock

from klient import KafkaProducer, ProducerConfig, KafkaTransactionError


@patch('klient.producer.Producer')
def test_begin_commit_transaction(mock_underlying):
    # Mock underlying producer methods
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.commit_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-1'))
    begin_res = producer.begin_transaction()
    assert begin_res.success is True
    assert producer.in_transaction is True

    commit_res = producer.commit_transaction()
    assert commit_res.success is True
    assert producer.in_transaction is False

    instance.begin_transaction.assert_called_once()
    instance.commit_transaction.assert_called_once()


@patch('klient.producer.Producer')
def test_abort_transaction(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.abort_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-2'))
    producer.begin_transaction()
    assert producer.in_transaction is True

    abort_res = producer.abort_transaction()
    assert abort_res.success is True
    assert producer.in_transaction is False
    instance.abort_transaction.assert_called_once()


@patch('klient.producer.Producer')
def test_transaction_context_manager_commit(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.commit_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-ctx'))
    with producer.transaction():
        producer.produce(topic='demo', value='msg', flush=False)
        # In transaction after begin
        assert producer.in_transaction is True
    # After context exit committed
    assert producer.in_transaction is False
    instance.commit_transaction.assert_called_once()


@patch('klient.producer.Producer')
def test_transaction_context_manager_abort_on_exception(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.abort_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-ctx-abort'))
    with pytest.raises(RuntimeError):
        with producer.transaction():
            raise RuntimeError('fail inside tx')
    instance.abort_transaction.assert_called_once()
    assert producer.in_transaction is False


@patch('klient.producer.Producer')
@pytest.mark.asyncio
async def test_async_transaction_context_manager_commit(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.commit_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-async'))
    async with producer.atransaction():
        await producer.aproduce(topic='demo', value='msg', flush=False)
        assert producer.in_transaction is True
    assert producer.in_transaction is False
    instance.commit_transaction.assert_called_once()


@patch('klient.producer.Producer')
@pytest.mark.asyncio
async def test_async_transaction_context_manager_abort(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None
    instance.abort_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-async-abort'))
    with pytest.raises(ValueError):
        async with producer.atransaction():
            raise ValueError('boom')
    instance.abort_transaction.assert_called_once()
    assert producer.in_transaction is False


@patch('klient.producer.Producer')
def test_error_on_double_begin(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.begin_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-double'))
    producer.begin_transaction()
    with pytest.raises(KafkaTransactionError):
        producer.begin_transaction()


@patch('klient.producer.Producer')
def test_error_commit_without_begin(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.commit_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-no-begin'))
    with pytest.raises(KafkaTransactionError):
        producer.commit_transaction()


@patch('klient.producer.Producer')
def test_error_abort_without_begin(mock_underlying):
    instance = MagicMock()
    mock_underlying.return_value = instance
    instance.abort_transaction.return_value = None

    producer = KafkaProducer(ProducerConfig(bootstrap_servers='localhost:9092', transactional_id='tx-no-begin'))
    with pytest.raises(KafkaTransactionError):
        producer.abort_transaction()
