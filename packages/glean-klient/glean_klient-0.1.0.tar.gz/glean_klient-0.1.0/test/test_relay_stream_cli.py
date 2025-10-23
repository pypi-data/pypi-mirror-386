import pytest
from click.testing import CliRunner
from klient.metrics import snapshot
from klient.__main__ import cli

class DummyRelayConsumer:
    def __init__(self, total=3):
        self._is_running = True
        self._poll_count = 0
        self._total = total
        self._stopped = False
    def subscribe(self, topics):
        assert isinstance(topics, list)
    def poll_message(self, timeout: float):
        if self._poll_count >= self._total:
            return None
        self._poll_count += 1
        class Msg:
            topic = 'source'
            partition = 0
            offset = self._poll_count
            key = b'k'
            value = f'value-{self._poll_count}'.encode()
            is_transactional = False
            transaction_id = None
        return Msg()
    def commit(self):
        return None
    def stop(self):
        self._is_running = False
        self._stopped = True

class DummyRelayProducer:
    def __init__(self):
        self._in_transaction = False
        self._produced = []
        self.transactional_id = 'relay-tx'
    def begin_transaction(self):
        self._in_transaction = True
        return None
    def commit_transaction(self):
        self._in_transaction = False
        class CommitRes:
            duration_ms = 1.2
        return CommitRes()
    def abort_transaction(self):
        self._in_transaction = False
    def produce(self, **kwargs):
        self._produced.append(kwargs)
    def close(self):
        pass
    @property
    def in_transaction(self):
        return self._in_transaction

@pytest.fixture(autouse=True)
def patch_builders(monkeypatch):
    from klient import __main__ as main_mod
    monkeypatch.setattr(main_mod, 'build_consumer', lambda *a, **kw: DummyRelayConsumer(total=3))
    monkeypatch.setattr(main_mod, 'build_producer', lambda *a, **kw: DummyRelayProducer())
    yield


def test_relay_stream_commits_batch(monkeypatch):
    # speed up loop by removing sleeps
    import time as _time
    monkeypatch.setattr(_time, 'sleep', lambda *_a, **_kw: None)

    runner = CliRunner()
    result = runner.invoke(cli, ['relay', 'stream', 'source', 'target', '--batch-size', '3', '--timeout', '0', '--grace-period', '0', '--max-batches', '1'])
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.splitlines() if line.startswith('{')]
    assert any('relay_batch_committed' in line for line in lines), lines
    snap = snapshot()
    assert snap.get('relay.batch.commit', 0) >= 1
    assert snap.get('relay.messages.forwarded', 0) >= 3
