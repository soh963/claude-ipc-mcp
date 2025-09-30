from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re


INSTANCE_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")


def validate_instance_id(value: str) -> bool:
    return bool(INSTANCE_RE.match(value or ""))


@dataclass(frozen=True)
class Address:
    instance: str
    project: Optional[str] = None

    def __post_init__(self):
        if not validate_instance_id(self.instance):
            raise ValueError("invalid instance id")


@dataclass(frozen=True)
class Handshake:
    instance_id: str
    session_token: Optional[str]

    def __post_init__(self):
        if not validate_instance_id(self.instance_id):
            raise ValueError("invalid instance id")
