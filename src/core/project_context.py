from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SessionState:
    instance_id: str
    session_token: str


def project_root(start: Path | None = None) -> Path:
    return (start or Path.cwd()).resolve()


def ipc_root(root: Path | None = None) -> Path:
    return project_root(root) / ".ipc"


def ensure_layout(root: Path | None = None) -> None:
    r = ipc_root(root)
    for s in ("config", "logs", "state", "secret"):
        (r / s).mkdir(parents=True, exist_ok=True)


def state_file(root: Path | None = None) -> Path:
    return ipc_root(root) / "state" / "session.json"


def read_session(root: Path | None = None) -> Optional[SessionState]:
    sf = state_file(root)
    if not sf.exists():
        return None
    try:
        data = json.loads(sf.read_text(encoding="utf-8"))
        if data.get("instance_id") and data.get("session_token"):
            return SessionState(instance_id=data["instance_id"], session_token=data["session_token"]) 
    except Exception:
        return None
    return None


def write_session(instance_id: str, session_token: str, root: Path | None = None) -> None:
    ensure_layout(root)
    sf = state_file(root)
    payload = {"instance_id": instance_id, "session_token": session_token}
    sf.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def default_instance_id(root: Path | None = None) -> str:
    # Derive from folder name, sanitized to 32 chars with allowed charset
    name = project_root(root).name
    import re
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", name)[:32]
    if not sanitized:
        sanitized = "project"
    return sanitized
