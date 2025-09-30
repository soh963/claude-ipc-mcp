from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Optional
import uuid


@dataclass(frozen=True)
class Message:
    id: str
    from_id: str
    to_id: str
    topic: Optional[str]
    payload: Any
    ts: datetime
    corr_id: Optional[str] = None
    session_token: Optional[str] = None

    @staticmethod
    def new(
        from_id: str,
        to_id: str,
        payload: Any,
        topic: Optional[str] = None,
        corr_id: Optional[str] = None,
    ) -> "Message":
        return Message(
            id=str(uuid.uuid4()),
            from_id=from_id,
            to_id=to_id,
            topic=topic,
            payload=payload,
            ts=datetime.now(UTC),
            corr_id=corr_id,
            session_token=None,
        )
