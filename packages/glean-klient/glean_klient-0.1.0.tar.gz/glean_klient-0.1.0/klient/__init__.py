"""Kafka client wrapper library supporting both synchronous and asynchronous operations.

Provides high-level interfaces for:
- Synchronous and asynchronous message consumption
- Synchronous and asynchronous message production
- Transaction support (begin/commit/abort + context managers)
- Topic and cluster administration
- Unified environment-based configuration loading utilities

Environment configuration loader utilities are defined first to avoid circular
import issues when producer/consumer/admin modules import them.
"""

from pathlib import Path
import json
import os
import typing as t

def _load_raw_config_file(path: Path) -> t.Dict[str, t.Any]:
    if not path.exists():
        return {}
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {path}: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read config file {path}: {e}")

def resolve_env_config(env: t.Optional[str], explicit_file: t.Optional[str]) -> t.Dict[str, t.Any]:
    """Resolve configuration from a SINGLE JSON file with default + environment sections.

    Model:
      - Exactly one file supplies configuration: either `explicit_file` if provided,
        else `~/.kafka/config.json`.
      - File may contain a `default` object and any number of named environment objects.
      - When `env` is specified, effective config = merge of `default` (if present) overlaid
        by the named environment object. Key collisions favor the environment.
      - When `env` is not specified, returns the `default` object if present else the raw top-level mapping.

    Example structure:
    {
      "default": {"bootstrap.servers": "localhost:9092", "acks": "all"},
      "prod": {"bootstrap.servers": "prod-broker:9092", "compression.type": "lz4"},
      "dev": {"bootstrap.servers": "dev-broker:9092"}
    }

    Topic names MUST NOT appear in this file. Returns empty dict if file missing or invalid.
    """
    home_dir = Path(os.path.expanduser('~')) / '.kafka'
    path = Path(explicit_file) if explicit_file else home_dir / 'config.json'
    raw = _load_raw_config_file(path)
    if not isinstance(raw, dict):
        return {}
    # Legacy compatibility: allow per-env standalone file ~/.kafka/{env}.json if config.json missing
    if not explicit_file and env and not raw and (home_dir / f"{env}.json").exists():
        env_raw = _load_raw_config_file(home_dir / f"{env}.json")
        return env_raw if isinstance(env_raw, dict) else {}
    default_section = raw.get('default') if isinstance(raw.get('default'), dict) else {}
    if env:
        from typing import cast, Dict, Any
        env_section_raw = raw.get(env) if isinstance(raw.get(env), dict) else {}
        # If no default/env structured sections present, and raw looks like direct config, return raw mapping unchanged
        if not default_section and not env_section_raw and 'bootstrap.servers' in raw:
            return raw
        default_cast: Dict[str, Any] = cast(Dict[str, Any], default_section if isinstance(default_section, dict) else {})
        env_cast: Dict[str, Any] = cast(Dict[str, Any], env_section_raw if isinstance(env_section_raw, dict) else {})
        merged: Dict[str, Any] = dict(default_cast)
        merged.update(env_cast)
        # If env not found, fall back to default_cast
        return merged if env_cast else default_cast
    # No env requested: return default section if present else raw mapping
    return default_section or raw

def split_env_config(raw: t.Dict[str, t.Any]) -> t.Tuple[t.Dict[str, t.Any], t.Dict[str, t.Any], t.Dict[str, t.Any]]:
    if not raw:
        return {}, {}, {}
    common = raw.get('common', {}) if isinstance(raw.get('common'), dict) else {}
    def _section(name: str) -> t.Dict[str, t.Any]:
        sec = raw.get(name, {})
        return sec if isinstance(sec, dict) else {}
    prod = {**common, **_section('producer')}
    cons = {**common, **_section('consumer')}
    adm = {**common, **_section('admin')}
    if not prod and not cons and not adm and not common:
        return raw, raw, raw
    return prod, cons, adm

def extract_bootstrap(raw_sections: t.Sequence[t.Dict[str, t.Any]]) -> t.Optional[str]:
    for section in raw_sections:
        if 'bootstrap.servers' in section:
            return section['bootstrap.servers']
    return None

from .producer import KafkaProducer, ProducerConfig, ProduceResult, KafkaProducerError, TransactionResult, KafkaTransactionError  # noqa: E402
from .consumer import KafkaConsumer, ConsumerConfig, MessageResult, KafkaConsumerError  # noqa: E402
from .admin import KafkaAdmin, AdminConfig, TopicMetadata, KafkaAdminError  # noqa: E402

__version__ = "0.1.0"

__all__ = [
    'KafkaProducer','ProducerConfig','ProduceResult','KafkaProducerError','KafkaTransactionError','TransactionResult',
    'KafkaConsumer','ConsumerConfig','MessageResult','KafkaConsumerError',
    'KafkaAdmin','AdminConfig','KafkaAdminError','TopicMetadata',
    'resolve_env_config','split_env_config','extract_bootstrap'
]