from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass(frozen=True)
class Responder:
    name: str
    role: Literal["system", "assistant", "tool", "user"]
    topics: List[str]
    status: Optional[str] = None  # e.g., running, stopped
