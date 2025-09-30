from __future__ import annotations

import pytest

from src.core.models.routing import validate_instance_id, Address, Handshake


@pytest.mark.parametrize(
    "value,expected",
    [
        ("abc", True),
        ("ABC_123-xyz", True),
        ("", False),
        ("toolongtoolongtoolongtoolongtoolong", False),
        ("bad space", False),
    ],
)
def test_validate_instance_id(value: str, expected: bool):
    assert validate_instance_id(value) is expected


def test_address_rejects_invalid_instance():
    with pytest.raises(ValueError):
        Address(instance="bad space")


def test_handshake_validation():
    hs = Handshake(instance_id="ok123", session_token=None)
    assert hs.instance_id == "ok123"
    assert hs.session_token is None

    with pytest.raises(ValueError):
        Handshake(instance_id="bad space", session_token=None)
