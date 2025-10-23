"""Lightweight in-process metrics for klient.

Provides simple counters stored in a module-level registry. Designed for unit tests and
basic observability hooks without external dependencies.
"""

from typing import Dict
import threading

_lock = threading.Lock()
_counters: Dict[str, int] = {
    "producer.retry": 0,
    "producer.tx.begin": 0,
    "producer.tx.commit": 0,
    "producer.tx.abort": 0,
    "consumer.rebalance.assign": 0,
    "consumer.rebalance.revoke": 0,
    "consumer.rebalance.lost": 0,
    "consumer.shutdown.signal": 0,
    "consumer.shutdown.complete": 0,
    "relay.messages.forwarded": 0,
    "relay.batch.commit": 0,
}

def inc(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + value

def get(name: str) -> int:
    return _counters.get(name, 0)

def snapshot() -> Dict[str, int]:
    with _lock:
        return dict(_counters)
