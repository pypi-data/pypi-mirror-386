import json
from pathlib import Path

import pytest

from klient import resolve_env_config as _resolve_env_config, split_env_config as _split_env_config


@pytest.fixture()
def temp_kafka_dir(tmp_path, monkeypatch):
    d = tmp_path / ".kafka"
    d.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    return d


def write_json(path: Path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_resolve_env_config_default_only(temp_kafka_dir):
    cfg = {"default": {"bootstrap.servers": "dev:9092", "foo": "bar"}}
    write_json(temp_kafka_dir / "config.json", cfg)
    resolved = _resolve_env_config(env=None, explicit_file=None)
    assert resolved == cfg["default"]


def test_resolve_env_config_default_and_env_merge(temp_kafka_dir):
    cfg = {
        "default": {"bootstrap.servers": "dev:9092", "security.protocol": "ssl", "foo": "base"},
        "sit": {"bootstrap.servers": "sit:9092", "foo": "override", "bar": "value"},
    }
    write_json(temp_kafka_dir / "config.json", cfg)
    resolved = _resolve_env_config(env="sit", explicit_file=None)
    # Merge semantics: default + env (env overrides duplicates)
    assert resolved["bootstrap.servers"] == "sit:9092"
    assert resolved["security.protocol"] == "ssl"
    assert resolved["foo"] == "override"
    assert resolved["bar"] == "value"
    # Should not contain nested 'default' or 'sit' keys anymore
    assert "default" not in resolved
    assert "sit" not in resolved


def test_resolve_env_config_explicit_file_no_merge(tmp_path):
    explicit = tmp_path / "explicit.json"
    data = {"bootstrap.servers": "explicit:9092", "value": 1}
    write_json(explicit, data)
    resolved = _resolve_env_config(env="whatever", explicit_file=str(explicit))
    assert resolved == data


def test_resolve_env_config_explicit_with_sections(tmp_path):
    explicit = tmp_path / "explicit_sections.json"
    data = {
        "default": {"bootstrap.servers": "dev:9092", "x": 1},
        "prod": {"bootstrap.servers": "prod:9092", "x": 2, "y": 3},
    }
    write_json(explicit, data)
    resolved = _resolve_env_config(env="prod", explicit_file=str(explicit))
    assert resolved["bootstrap.servers"] == "prod:9092"
    assert resolved["x"] == 2  # override
    assert resolved["y"] == 3


def test_resolve_env_config_env_file_direct(temp_kafka_dir):
    env_data = {"bootstrap.servers": "direct-env:9092", "a": 5}
    write_json(temp_kafka_dir / "qa.json", env_data)
    resolved = _resolve_env_config(env="qa", explicit_file=None)
    assert resolved == env_data


def test_split_env_config_with_sections():
    raw = {
        "common": {"client.id": "cid", "statistics.interval.ms": 1000},
        "producer": {"compression.type": "lz4"},
        "consumer": {"group.id": "g1"},
        "admin": {"request.timeout.ms": 45000},
    }
    prod, cons, adm = _split_env_config(raw)
    # Producer includes common + its override
    assert prod["client.id"] == "cid"
    assert prod["compression.type"] == "lz4"
    # Consumer includes common + consumer keys
    assert cons["group.id"] == "g1"
    assert cons["client.id"] == "cid"
    # Admin includes common + admin keys
    assert adm["request.timeout.ms"] == 45000
    assert adm["client.id"] == "cid"


def test_split_env_config_no_role_sections():
    raw = {"bootstrap.servers": "plain:9092", "x": 1}
    prod, cons, adm = _split_env_config(raw)
    # When no distinct sections, raw passed through to all
    assert prod == raw
    assert cons == raw
    assert adm == raw


def test_merge_behavior_preserves_non_overridden_keys(temp_kafka_dir):
    cfg = {
        "default": {"a": 1, "b": 2},
        "envx": {"b": 20, "c": 30},
    }
    write_json(temp_kafka_dir / "config.json", cfg)
    resolved = _resolve_env_config(env="envx", explicit_file=None)
    assert resolved == {"a": 1, "b": 20, "c": 30}


def test_missing_config_file_returns_empty(temp_kafka_dir):
    # Remove config.json if it exists
    cfg_file = temp_kafka_dir / "config.json"
    if cfg_file.exists():
        cfg_file.unlink()
    resolved = _resolve_env_config(env=None, explicit_file=None)
    assert resolved == {}
