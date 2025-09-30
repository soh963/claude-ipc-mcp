from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from src.core.models.message import Message


def test_message_new_factory_sets_fields():
    m = Message.new(from_id="a", to_id="b", payload={"x": 1}, topic="chat", corr_id="c1")
    # id is UUID string
    uuid.UUID(m.id)
    assert m.from_id == "a"
    assert m.to_id == "b"
    assert m.topic == "chat"
    assert m.payload == {"x": 1}
    assert isinstance(m.ts, datetime)
    assert m.corr_id == "c1"
    assert m.session_token is None


def test_message_immutability_dataclass():
    m = Message.new(from_id="a", to_id="b", payload=1)
    # dataclass is frozen; attempting to mutate should raise
    try:
        setattr(m, "to_id", "c")
        raised = False
    except Exception:
        raised = True
    assert raised is True
