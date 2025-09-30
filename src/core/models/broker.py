from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Optional


@dataclass(frozen=True)
class Broker:
    version: str
    port: int
    started_at: Optional[datetime] = None

    @staticmethod
    def from_env(default_version: str = "0.0.0") -> "Broker":
        port_s = os.environ.get("IPC_BROKER_PORT", "9876")
        try:
            port = int(port_s)
        except Exception:
            port = 9876
        return Broker(version=default_version, port=port, started_at=None)
