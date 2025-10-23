"""Tests for consumer seek functionality."""
from unittest.mock import MagicMock

import pytest

from klient import KafkaConsumer, KafkaConsumerError, ConsumerConfig


def test_seek_to_offset_valid_parameters():
    """Test that seek_to_offset calls the underlying consumer seek method with correct TopicPartition."""
    mock_consumer = MagicMock()
    
    config = ConsumerConfig(
        bootstrap_servers='localhost:9092',
        group_id='test-group'
    )
    consumer = KafkaConsumer(config=config)
    consumer._consumer = mock_consumer
    
    # Call seek_to_offset with specific partition
    consumer.seek_to_offset("test-topic", 1000, partition=0)
    
    # Verify that seek was called with correct TopicPartition
    mock_consumer.seek.assert_called_once()
    call_args = mock_consumer.seek.call_args[0][0]
    assert call_args.topic == "test-topic"
    assert call_args.partition == 0
    assert call_args.offset == 1000


def test_seek_to_offset_invalid_negative_partition():
    """Test that seek_to_offset raises error for negative partition."""
    mock_consumer = MagicMock()
    
    config = ConsumerConfig(
        bootstrap_servers='localhost:9092',
        group_id='test-group'
    )
    consumer = KafkaConsumer(config=config)
    consumer._consumer = mock_consumer
    
    with pytest.raises(KafkaConsumerError, match="Partition number must be non-negative"):
        consumer.seek_to_offset("test-topic", 1000, partition=-1)


def test_seek_to_offset_invalid_negative_offset():
    """Test that seek_to_offset raises error for negative offset."""
    mock_consumer = MagicMock()
    
    config = ConsumerConfig(
        bootstrap_servers='localhost:9092',
        group_id='test-group'
    )
    consumer = KafkaConsumer(config=config)
    consumer._consumer = mock_consumer
    
    with pytest.raises(KafkaConsumerError, match="Offset must be non-negative"):
        consumer.seek_to_offset("test-topic", -1, partition=0)


def test_seek_to_offset_handles_confluent_kafka_exception():
    """Test that seek_to_offset wraps confluent-kafka exceptions properly."""
    from confluent_kafka import KafkaException
    
    mock_consumer = MagicMock()
    mock_consumer.seek.side_effect = KafkaException("Seek failed")
    
    config = ConsumerConfig(
        bootstrap_servers='localhost:9092',
        group_id='test-group'
    )
    consumer = KafkaConsumer(config=config)
    consumer._consumer = mock_consumer
    
    with pytest.raises(KafkaConsumerError, match="Failed to seek to offset 1000 on partition 0"):
        consumer.seek_to_offset("test-topic", 1000, partition=0)


def test_seek_to_offset_all_partitions():
    """Test that seek_to_offset seeks to all partitions when partition is not specified."""
    from unittest.mock import MagicMock
    
    mock_consumer = MagicMock()
    
    # Mock the topic metadata response
    mock_topic_metadata = MagicMock()
    mock_topic_metadata.partitions = {0: None, 1: None, 2: None}  # 3 partitions
    
    mock_cluster_metadata = MagicMock()
    mock_cluster_metadata.topics = {"test-topic": mock_topic_metadata}
    
    mock_consumer.list_topics.return_value = mock_cluster_metadata
    
    config = ConsumerConfig(
        bootstrap_servers='localhost:9092',
        group_id='test-group'
    )
    consumer = KafkaConsumer(config=config)
    consumer._consumer = mock_consumer
    
    # Call seek_to_offset without specifying partition
    consumer.seek_to_offset("test-topic", 1000)
    
    # Verify that seek was called 3 times (once for each partition)
    assert mock_consumer.seek.call_count == 3
    
    # Verify the calls were made with correct TopicPartitions
    calls = mock_consumer.seek.call_args_list
    for partition_id in range(3):
        call_args = calls[partition_id][0][0]
        assert call_args.topic == "test-topic"
        assert call_args.partition == partition_id
        assert call_args.offset == 1000