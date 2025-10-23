import json
import tempfile
from pathlib import Path

from klient import resolve_env_config

def test_multi_role_env_distinct_sections():
    config_data = {
        "default": {"bootstrap.servers": "base:9092", "linger.ms": 5},
        "prod-producer": {"bootstrap.servers": "prod-producer:9092", "compression.type": "lz4", "linger.ms": 10},
        "prod-consumer": {"bootstrap.servers": "prod-consumer:9092", "auto.offset.reset": "earliest"},
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / 'config.json'
        config_path.write_text(json.dumps(config_data), encoding='utf-8')
        producer_effective = resolve_env_config('prod-producer', str(config_path))
        consumer_effective = resolve_env_config('prod-consumer', str(config_path))
        assert producer_effective['bootstrap.servers'] == 'prod-producer:9092'
        assert producer_effective['compression.type'] == 'lz4'
        # default key overridden
        assert producer_effective['linger.ms'] == 10
        # consumer env inherits default linger.ms if not overridden
        assert consumer_effective['bootstrap.servers'] == 'prod-consumer:9092'
        assert consumer_effective['auto.offset.reset'] == 'earliest'
        assert consumer_effective['linger.ms'] == 5
