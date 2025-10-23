import json
import tempfile
from pathlib import Path

from klient import resolve_env_config

def test_single_file_env_merge_dev():
    data = {
        "default": {"bootstrap.servers": "localhost:9092", "acks": "all", "compression.type": "none"},
        "dev": {"bootstrap.servers": "dev-broker:9092", "compression.type": "lz4"}
    }
    with tempfile.TemporaryDirectory() as td:
        cfg_path = Path(td) / 'config.json'
        cfg_path.write_text(json.dumps(data), encoding='utf-8')
        merged = resolve_env_config('dev', str(cfg_path))
        assert merged["bootstrap.servers"] == "dev-broker:9092"  # env override
        assert merged["acks"] == "all"  # default carried over
        assert merged["compression.type"] == "lz4"  # env override


def test_single_file_env_no_env_returns_default():
    data = {
        "default": {"bootstrap.servers": "localhost:9092", "client.id": "base"},
        "prod": {"bootstrap.servers": "prod-broker:9092"}
    }
    with tempfile.TemporaryDirectory() as td:
        cfg_path = Path(td) / 'config.json'
        cfg_path.write_text(json.dumps(data), encoding='utf-8')
        merged = resolve_env_config(None, str(cfg_path))
        assert merged["bootstrap.servers"] == "localhost:9092"
        assert merged["client.id"] == "base"
        assert "prod" not in merged  # ensure we did not return full mapping


def test_single_file_env_missing_default_fallback():
    data = {"dev": {"bootstrap.servers": "dev-broker:9092", "enable.idempotence": True}}
    with tempfile.TemporaryDirectory() as td:
        cfg_path = Path(td) / 'config.json'
        cfg_path.write_text(json.dumps(data), encoding='utf-8')
        merged = resolve_env_config('dev', str(cfg_path))
        assert merged["bootstrap.servers"] == "dev-broker:9092"
        assert merged.get("enable.idempotence") is True


def test_single_file_env_unknown_env_returns_default_only():
    data = {
        "default": {"bootstrap.servers": "localhost:9092", "retries": 3},
        "prod": {"bootstrap.servers": "prod-broker:9092"}
    }
    with tempfile.TemporaryDirectory() as td:
        cfg_path = Path(td) / 'config.json'
        cfg_path.write_text(json.dumps(data), encoding='utf-8')
        merged = resolve_env_config('staging', str(cfg_path))
        # staging not found; should behave like no env (return default)
        assert merged["bootstrap.servers"] == "localhost:9092"
        assert merged["retries"] == 3
