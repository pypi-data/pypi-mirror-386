"""
Basic tests for the Kafka client wrapper library.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Try to import klient, if it fails, add the project root to path and try again
try:
    from klient import (
        ConsumerConfig, ProducerConfig, AdminConfig,
        KafkaConsumer, KafkaProducer, KafkaAdmin,
        MessageResult, ProduceResult, TopicMetadata
    )
except ImportError:
    # Add the project root to the path so we can import klient
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from klient import (
        ConsumerConfig, ProducerConfig, AdminConfig,
        KafkaConsumer, KafkaProducer, KafkaAdmin,
        MessageResult, ProduceResult, TopicMetadata
    )


class TestConfigurations:
    """Test configuration classes."""
    
    def test_consumer_config_creation(self):
        """Test ConsumerConfig creation and conversion."""
        config = ConsumerConfig(
            bootstrap_servers="localhost:9092",
            group_id="test-group"
        )
        
        confluent_config = config.to_confluent_config()
        
        assert confluent_config['bootstrap.servers'] == "localhost:9092"
        assert confluent_config['group.id'] == "test-group"
        assert confluent_config['auto.offset.reset'] == "earliest"
        assert confluent_config['enable.auto.commit'] is True
    
    def test_producer_config_creation(self):
        """Test ProducerConfig creation and conversion."""
        config = ProducerConfig(
            bootstrap_servers="localhost:9092",
            acks="all"
        )
        
        confluent_config = config.to_confluent_config()
        
        assert confluent_config['bootstrap.servers'] == "localhost:9092"
        assert confluent_config['acks'] == "all"
        assert confluent_config['enable.idempotence'] is True
    
    def test_admin_config_creation(self):
        """Test AdminConfig creation and conversion."""
        config = AdminConfig(
            bootstrap_servers="localhost:9092",
            request_timeout_ms=60000
        )
        
        confluent_config = config.to_confluent_config()
        
        assert confluent_config['bootstrap.servers'] == "localhost:9092"
        assert confluent_config['request.timeout.ms'] == 60000


class TestMessageResult:
    """Test MessageResult class."""
    
    def test_message_result_creation(self):
        """Test MessageResult creation."""
        result = MessageResult(
            topic="test-topic",
            partition=0,
            offset=123,
            key=b"test-key",
            value=b"test-value",
            timestamp=(1, 1634567890000),
            headers={"header1": b"value1"}
        )
        
        assert result.topic == "test-topic"
        assert result.partition == 0
        assert result.offset == 123
        assert result.key == b"test-key"
        assert result.value == b"test-value"
        assert result.headers == {"header1": b"value1"}


class TestProduceResult:
    """Test ProduceResult class."""
    
    def test_produce_result_success(self):
        """Test successful ProduceResult."""
        result = ProduceResult(
            topic="test-topic",
            partition=0,
            offset=456,
            success=True
        )
        
        assert result.topic == "test-topic"
        assert result.partition == 0
        assert result.offset == 456
        assert result.success is True
        assert result.error is None
    
    def test_produce_result_failure(self):
        """Test failed ProduceResult."""
        result = ProduceResult(
            topic="test-topic",
            partition=-1,
            offset=-1,
            success=False,
            error="Connection failed"
        )
        
        assert result.success is False
        assert result.error == "Connection failed"


class TestTopicMetadata:
    """Test TopicMetadata class."""
    
    def test_topic_metadata_creation(self):
        """Test TopicMetadata creation."""
        metadata = TopicMetadata(
            name="test-topic",
            partitions=3,
            replication_factor=1,
            config={"cleanup.policy": "delete"}
        )
        
        assert metadata.name == "test-topic"
        assert metadata.partitions == 3
        assert metadata.replication_factor == 1
        assert metadata.config == {"cleanup.policy": "delete"}


@patch('klient.consumer.Consumer')
class TestKafkaConsumer:
    """Test KafkaConsumer class."""
    
    def test_consumer_creation(self, mock_consumer_class):
        """Test KafkaConsumer creation."""
        config = ConsumerConfig(
            bootstrap_servers="localhost:9092",
            group_id="test-group"
        )
        
        consumer = KafkaConsumer(config)
        
        assert consumer.config == config
        assert consumer._consumer is None
        assert consumer._is_running is False
    
    def test_context_manager(self, mock_consumer_class):
        """Test KafkaConsumer as context manager."""
        config = ConsumerConfig(
            bootstrap_servers="localhost:9092",
            group_id="test-group"
        )
        
        with KafkaConsumer(config) as consumer:
            assert isinstance(consumer, KafkaConsumer)


@patch('klient.producer.Producer')
class TestKafkaProducer:
    """Test KafkaProducer class."""
    
    def test_producer_creation(self, mock_producer_class):
        """Test KafkaProducer creation."""
        config = ProducerConfig(bootstrap_servers="localhost:9092")
        
        producer = KafkaProducer(config)
        
        assert producer.config == config
        assert producer._producer is None
    
    def test_context_manager(self, mock_producer_class):
        """Test KafkaProducer as context manager."""
        config = ProducerConfig(bootstrap_servers="localhost:9092")
        
        with KafkaProducer(config) as producer:
            assert isinstance(producer, KafkaProducer)


@patch('klient.admin.AdminClient')
class TestKafkaAdmin:
    """Test KafkaAdmin class."""
    
    def test_admin_creation(self, mock_admin_class):
        """Test KafkaAdmin creation."""
        config = AdminConfig(bootstrap_servers="localhost:9092")
        
        admin = KafkaAdmin(config)
        
        assert admin.config == config
        assert admin._admin is None


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Test async functionality."""
    
    @patch('klient.consumer.Consumer')
    async def test_async_poll_message(self, mock_consumer_class):
        """Test async message polling."""
        config = ConsumerConfig(
            bootstrap_servers="localhost:9092",
            group_id="test-group"
        )
        
        consumer = KafkaConsumer(config)
        
        # Mock the poll_message method to return None
        consumer.poll_message = Mock(return_value=None)
        
        result = await consumer.apoll_message(timeout=1.0)
        
        assert result is None
        consumer.poll_message.assert_called_once_with(1.0)
    
    @patch('klient.producer.Producer')
    async def test_async_produce(self, mock_producer_class):
        """Test async message production."""
        config = ProducerConfig(bootstrap_servers="localhost:9092")
        
        producer = KafkaProducer(config)
        
        # Mock the produce method
        producer.produce = Mock(return_value=None)
        
        await producer.aproduce(
            topic="test-topic",
            value="test-message",
            flush=True
        )
        
        producer.produce.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])