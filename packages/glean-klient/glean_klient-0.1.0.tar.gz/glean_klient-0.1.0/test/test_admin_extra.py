from unittest.mock import patch, MagicMock

from klient import KafkaAdmin, AdminConfig, TopicMetadata

@patch('klient.admin.AdminClient')
def test_list_topics(mock_admin):
    instance = MagicMock()
    mock_admin.return_value = instance
    # Simulate metadata listing
    instance.list_topics.return_value.topics = {'t1': MagicMock(), 't2': MagicMock()}
    admin = KafkaAdmin(AdminConfig(bootstrap_servers='localhost:9092'))
    topics = admin.list_topics()
    assert set(topics) == {'t1', 't2'}

@patch('klient.admin.AdminClient')
def test_describe_topics(mock_admin):
    instance = MagicMock()
    mock_admin.return_value = instance
    # list_topics returns metadata with .topics dict
    metadata = MagicMock()
    topic_meta = MagicMock()
    part = MagicMock()
    part.replicas = [MagicMock(), MagicMock()]
    topic_meta.partitions = {0: part}
    metadata.topics = {'demo': topic_meta}
    instance.list_topics.return_value = metadata
    # describe_configs returns mapping from ConfigResource -> future
    config_future = MagicMock()
    config_future.result.return_value = {}
    def describe_configs(resources):
        return {resources[0]: config_future}
    instance.describe_configs.side_effect = describe_configs
    admin = KafkaAdmin(AdminConfig(bootstrap_servers='localhost:9092'))
    details = admin.describe_topics(['demo'])
    assert 'demo' in details
    info = details['demo']
    assert info.partitions == 1

@patch('klient.admin.AdminClient')
def test_create_delete_topics(mock_admin):
    instance = MagicMock()
    mock_admin.return_value = instance
    # Futures simulation
    future_create = MagicMock()
    future_create.result.return_value = None
    instance.create_topics.return_value = {'newt': future_create}
    future_delete = MagicMock()
    future_delete.result.return_value = None
    instance.delete_topics.return_value = {'newt': future_delete}
    admin = KafkaAdmin(AdminConfig(bootstrap_servers='localhost:9092'))
    create_res = admin.create_topics([TopicMetadata(name='newt', partitions=1, replication_factor=1)])
    assert create_res['newt'] is True
    delete_res = admin.delete_topics(['newt'])
    assert delete_res['newt'] is True

@patch('klient.admin.AdminClient')
def test_cluster_metadata(mock_admin):
    instance = MagicMock()
    mock_admin.return_value = instance
    md = MagicMock()
    md.brokers = {'b1': MagicMock()}
    md.topics = {'t1': MagicMock()}
    instance.list_topics.return_value = md
    admin = KafkaAdmin(AdminConfig(bootstrap_servers='localhost:9092'))
    meta = admin.get_cluster_metadata()
    assert 'brokers' in meta and 'topics' in meta
