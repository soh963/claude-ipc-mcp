from __future__ import annotations

import os
from datetime import datetime

import pytest

from src.core.models.broker import Broker


def test_broker_from_env_uses_port_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("IPC_BROKER_PORT", "12345")
    b = Broker.from_env(default_version="1.2.3")
    assert b.port == 12345
    assert b.version == "1.2.3"
    assert b.started_at is None


def test_broker_from_env_defaults_when_invalid(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("IPC_BROKER_PORT", "not-a-number")
    b = Broker.from_env()
    assert b.port == 9876
    assert isinstance(b.version, str)
