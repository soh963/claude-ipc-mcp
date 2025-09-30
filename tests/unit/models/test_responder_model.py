from __future__ import annotations

from src.core.models.responder import Responder


def test_responder_fields_and_defaults():
    r = Responder(name="echo", role="tool", topics=["chat", "ping"])
    assert r.name == "echo"
    assert r.role == "tool"
    assert r.topics == ["chat", "ping"]
    assert r.status is None
