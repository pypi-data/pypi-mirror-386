import json
from pathlib import Path
import pytest

from klient import KafkaProducer, KafkaConsumer, KafkaAdmin, resolve_env_config


@pytest.fixture()
def kafka_home(tmp_path, monkeypatch):
    home = tmp_path / '.kafka'
    home.mkdir()
    monkeypatch.setenv('HOME', str(tmp_path))
    return home


def write(path: Path, data):
    path.write_text(json.dumps(data), encoding='utf-8')


def test_producer_from_env_config(kafka_home):
    cfg = {
        'default': {
            'bootstrap.servers': 'dev:9092',
            'statistics.interval.ms': 5000
        },
        'sit': {
            'bootstrap.servers': 'sit:9092',
            'compression.type': 'lz4',
            'transactional.id': 'tx-123'
        },
        'producer': {  # role section should still be merged
            'linger.ms': 5
        }
    }
    write(kafka_home / 'config.json', cfg)
    p = KafkaProducer.from_env_config(env='sit')
    confluent_cfg = p.config.to_confluent_config()
    assert confluent_cfg['bootstrap.servers'] == 'sit:9092'
    assert confluent_cfg['compression.type'] == 'lz4'
    # transactional enforced
    assert confluent_cfg['transactional.id'] == 'tx-123'
    assert p.supports_transactions is True


def test_consumer_from_env_config_requires_group(kafka_home):
    cfg = {
        'default': {'bootstrap.servers': 'dev:9092'},
        'consumer': {'auto.offset.reset': 'latest'}
    }
    write(kafka_home / 'config.json', cfg)
    with pytest.raises(ValueError):
        KafkaConsumer.from_env_config(env=None)  # no group.id supplied

    c = KafkaConsumer.from_env_config(env=None, group_id='g1')
    confluent_cfg = c.config.to_confluent_config()
    assert confluent_cfg['group.id'] == 'g1'
    assert confluent_cfg['bootstrap.servers'] == 'dev:9092'


def test_admin_from_env_config(kafka_home):
    cfg = {
        'default': {'bootstrap.servers': 'dev:9092'},
        'admin': {'request.timeout.ms': 45000}
    }
    write(kafka_home / 'config.json', cfg)
    a = KafkaAdmin.from_env_config(env=None)
    confluent_cfg = a.config.to_confluent_config()
    assert confluent_cfg['bootstrap.servers'] == 'dev:9092'
    assert confluent_cfg['request.timeout.ms'] == 30000  # default we passed (not overridden)


def test_resolve_env_merge(kafka_home):
    cfg = {
        'default': {'bootstrap.servers': 'dev:9092', 'security.protocol': 'ssl'},
        'prod': {'bootstrap.servers': 'prod:9092', 'ssl.ca.location': '/ca'}
    }
    write(kafka_home / 'config.json', cfg)
    merged = resolve_env_config('prod', None)
    assert merged['bootstrap.servers'] == 'prod:9092'
    assert merged['security.protocol'] == 'ssl'
    assert merged['ssl.ca.location'] == '/ca'
