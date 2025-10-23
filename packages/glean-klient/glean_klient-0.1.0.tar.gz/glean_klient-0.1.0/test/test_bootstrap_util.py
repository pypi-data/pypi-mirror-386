from klient import extract_bootstrap


def test_extract_bootstrap_first():
    bs = extract_bootstrap([
        {'x': 1},
        {'bootstrap.servers': 'host1:9092'},
        {'bootstrap.servers': 'host2:9092'},
    ])
    assert bs == 'host1:9092'


def test_extract_bootstrap_none():
    bs = extract_bootstrap([
        {'a': 1}, {'b': 2}
    ])
    assert bs is None
