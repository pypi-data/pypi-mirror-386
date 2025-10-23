"""
Kafka admin utilities for topic management and cluster information.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource
from . import resolve_env_config, split_env_config, extract_bootstrap


logger = logging.getLogger(__name__)


@dataclass
class AdminConfig:
    """Configuration for Kafka admin client."""
    bootstrap_servers: str
    request_timeout_ms: int = 30000
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_confluent_config(self) -> Dict[str, Any]:
        """Convert to confluent-kafka configuration format."""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'request.timeout.ms': self.request_timeout_ms,
        }
        config.update(self.additional_config)
        return config


@dataclass
class TopicMetadata:
    """Metadata information for a Kafka topic."""
    name: str
    partitions: int
    replication_factor: int
    config: Dict[str, str] = field(default_factory=dict)


class KafkaAdminError(Exception):
    """Custom exception for Kafka admin errors."""
    pass


class KafkaAdmin:
    """
    Kafka admin client wrapper for cluster and topic management.
    """
    
    def __init__(self, config: AdminConfig):
        """
        Initialize Kafka admin client.
        
        Args:
            config: Admin configuration
        """
        self.config = config
        self._admin = None

    @classmethod
    def from_env_config(
        cls,
        env: Optional[str] = None,
        config_file: Optional[str] = None,
        request_timeout_ms: int = 30000,
    ) -> 'KafkaAdmin':
        """Construct a KafkaAdmin from environment configuration."""
        raw = resolve_env_config(env, config_file)
        _, _, adm_raw = split_env_config(raw)
        effective_bootstrap = extract_bootstrap([adm_raw]) or 'localhost:9092'
        addl = dict(adm_raw)
        addl.pop('bootstrap.servers', None)
        cfg = AdminConfig(
            bootstrap_servers=effective_bootstrap,
            request_timeout_ms=request_timeout_ms,
            additional_config=addl,
        )
        return cls(cfg)
        
    def _create_admin(self) -> AdminClient:
        """Create and return a new AdminClient instance."""
        if self._admin is None:
            try:
                self._admin = AdminClient(self.config.to_confluent_config())
                logger.info("Created Kafka admin client")
            except Exception as e:
                logger.error(f"Failed to create Kafka admin client: {e}")
                raise KafkaAdminError(f"Failed to create admin client: {e}")
        return self._admin
    
    def create_topics(
        self, 
        topics: List[TopicMetadata], 
        timeout: float = 30.0,
        validate_only: bool = False
    ) -> Dict[str, bool]:
        """
        Create topics in Kafka.
        
        Args:
            topics: List of TopicMetadata objects
            timeout: Operation timeout in seconds
            validate_only: Only validate the request, don't create
            
        Returns:
            Dictionary mapping topic names to success status
        """
        admin = self._create_admin()
        
        new_topics = []
        for topic in topics:
            new_topic = NewTopic(
                topic.name,
                num_partitions=topic.partitions,
                replication_factor=topic.replication_factor,
                config=topic.config
            )
            new_topics.append(new_topic)
        
        try:
            futures = admin.create_topics(new_topics, validate_only=validate_only)
            
            results = {}
            for topic_name, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    results[topic_name] = True
                    logger.info(f"Successfully created topic: {topic_name}")
                except Exception as e:
                    results[topic_name] = False
                    logger.error(f"Failed to create topic {topic_name}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            raise KafkaAdminError(f"Topic creation error: {e}")
    
    def delete_topics(self, topic_names: List[str], timeout: float = 30.0) -> Dict[str, bool]:
        """
        Delete topics from Kafka.
        
        Args:
            topic_names: List of topic names to delete
            timeout: Operation timeout in seconds
            
        Returns:
            Dictionary mapping topic names to success status
        """
        admin = self._create_admin()
        
        try:
            futures = admin.delete_topics(topic_names)
            
            results = {}
            for topic_name, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    results[topic_name] = True
                    logger.info(f"Successfully deleted topic: {topic_name}")
                except Exception as e:
                    results[topic_name] = False
                    logger.error(f"Failed to delete topic {topic_name}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error deleting topics: {e}")
            raise KafkaAdminError(f"Topic deletion error: {e}")
    
    def list_topics(self, timeout: float = 30.0) -> List[str]:
        """
        List all topics in the Kafka cluster.
        
        Args:
            timeout: Operation timeout in seconds
            
        Returns:
            List of topic names
        """
        admin = self._create_admin()
        
        try:
            metadata = admin.list_topics(timeout=timeout)
            return list(metadata.topics.keys())
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            raise KafkaAdminError(f"List topics error: {e}")
    
    def describe_topics(self, topic_names: Optional[List[str]] = None, timeout: float = 30.0) -> Dict[str, TopicMetadata]:
        """
        Get detailed information about topics.
        
        Args:
            topic_names: Specific topics to describe (None for all topics)
            timeout: Operation timeout in seconds
            
        Returns:
            Dictionary mapping topic names to TopicMetadata
        """
        admin = self._create_admin()
        
        try:
            metadata = admin.list_topics(timeout=timeout)
            
            results = {}
            topics_to_describe = topic_names or list(metadata.topics.keys())
            
            for topic_name in topics_to_describe:
                if topic_name in metadata.topics:
                    topic_metadata = metadata.topics[topic_name]
                    
                    # Get topic configuration
                    config_resource = ConfigResource('topic', topic_name)
                    try:
                        config_futures = admin.describe_configs([config_resource])
                        config_result = config_futures[config_resource].result(timeout=timeout)
                        topic_config = {k: v.value for k, v in config_result.items()}
                    except Exception:
                        topic_config = {}
                    
                    results[topic_name] = TopicMetadata(
                        name=topic_name,
                        partitions=len(topic_metadata.partitions),
                        replication_factor=len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                        config=topic_config
                    )
            
            return results
            
        except Exception as e:
            logger.error(f"Error describing topics: {e}")
            raise KafkaAdminError(f"Describe topics error: {e}")
    
    def get_cluster_metadata(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        Get general cluster metadata information.
        
        Args:
            timeout: Operation timeout in seconds
            
        Returns:
            Dictionary with cluster metadata
        """
        admin = self._create_admin()
        
        try:
            metadata = admin.list_topics(timeout=timeout)
            
            return {
                'cluster_id': metadata.cluster_id,
                'controller_id': metadata.controller_id,
                'brokers': [
                    {
                        'id': broker.id,
                        'host': broker.host,
                        'port': broker.port
                    }
                    for broker in metadata.brokers.values()
                ],
                'topics_count': len(metadata.topics),
                'topics': list(metadata.topics.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster metadata: {e}")
            raise KafkaAdminError(f"Cluster metadata error: {e}")
    
    def topic_exists(self, topic_name: str, timeout: float = 30.0) -> bool:
        """
        Check if a topic exists.
        
        Args:
            topic_name: Name of the topic to check
            timeout: Operation timeout in seconds
            
        Returns:
            True if topic exists, False otherwise
        """
        try:
            topics = self.list_topics(timeout)
            return topic_name in topics
        except Exception as e:
            logger.error(f"Error checking if topic exists: {e}")
            return False