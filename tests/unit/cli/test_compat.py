import pytest

from core.compat import check_compat, is_restricted


def test_compat_same_minor():
    ok, msg = check_compat("2.0.0", "2.0.1")
    assert ok
    assert "Compatible" in msg
    assert not is_restricted("2.0.0", "2.0.1")


def test_compat_minor_skew_restricted():
    ok, msg = check_compat("2.1.0", "2.0.5")
    assert ok
    assert "restricted" in msg.lower()
    assert is_restricted("2.1.0", "2.0.5")


def test_compat_minor_too_far():
    ok, msg = check_compat("2.3.0", "2.0.0")
    assert not ok
    assert "Minor versions too far apart" in msg


essential_pairs = [
    ("2.0.0", "3.0.0"),
    ("1.9.9", "2.0.0"),
]


@pytest.mark.parametrize("cli,broker", essential_pairs)
def test_incompatible_major(cli, broker):
    ok, msg = check_compat(cli, broker)
    assert not ok
    assert "Incompatible major" in msg
