"""Utility helpers for managing IPC session files.

This module centralizes the logic for saving and loading per-instance session
files so that multiple AI agents can coexist on the same machine without
clobbering each other's authentication state.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

SESSION_PREFIX = ".ipc-session"
SESSION_DIR = Path.home()


@dataclass
class SessionData:
    instance_id: str
    session_token: str
    raw: dict
    path: Path


def _sanitize_instance_id(instance_id: str) -> str:
    """Return a filesystem-safe suffix for the given instance id."""
    cleaned = instance_id.strip()
    # Replace whitespace with dash and drop invalid filename characters.
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "-", cleaned)
    return cleaned or "default"


def session_path(instance_id: str) -> Path:
    """Compute the canonical session path for an instance."""
    return SESSION_DIR / f"{SESSION_PREFIX}-{_sanitize_instance_id(instance_id)}"


def default_session_path() -> Path:
    """Return the legacy single-session path."""
    return SESSION_DIR / SESSION_PREFIX


def list_session_files() -> Tuple[Path, ...]:
    """List all per-instance session files."""
    return tuple(sorted(SESSION_DIR.glob(f"{SESSION_PREFIX}-*")))


def save_session(instance_id: str, session_payload: dict, *, set_default: bool = True) -> Path:
    """Persist session data for the given instance.

    Args:
        instance_id: The logical agent identifier.
        session_payload: A JSON-serializable mapping containing at least
            ``instance_id`` and ``session_token``.
        set_default: When True, also refresh the legacy ``~/.ipc-session`` file
            for backward compatibility with older tooling.
    """
    target_path = session_path(instance_id)
    target_path.write_text(json.dumps(session_payload, indent=2))

    if set_default:
        default_path = default_session_path()
        default_path.write_text(json.dumps(session_payload, indent=2))

    return target_path


def load_session(instance_id: Optional[str] = None) -> SessionData:
    """Load session information for the specified instance.

    When ``instance_id`` is omitted, the loader will try the following in order:
    1. The legacy ``~/.ipc-session`` file if it exists.
    2. All per-instance files. If exactly one is present, it is used.

    Raises:
        FileNotFoundError: if no matching session file can be located.
        ValueError: if the located file is malformed.
    """
    candidate_path: Optional[Path] = None

    if instance_id:
        candidate_path = session_path(instance_id)
        if not candidate_path.exists():
            raise FileNotFoundError(
                f"Session file for '{instance_id}' not found at {candidate_path}. "
                "Register the instance first with tools/ipc_register.py."
            )
    else:
        # Prefer legacy default file for compatibility.
        default_path = default_session_path()
        if default_path.exists():
            candidate_path = default_path
        else:
            matches = list_session_files()
            if len(matches) == 1:
                candidate_path = matches[0]
            elif len(matches) > 1:
                available = ", ".join(path.name.replace(f"{SESSION_PREFIX}-", "") for path in matches)
                raise FileNotFoundError(
                    "Multiple session files detected. Specify an instance id with "
                    "--instance. Available instances: " + available
                )

    if not candidate_path or not candidate_path.exists():
        raise FileNotFoundError(
            "No session file found. Run tools/ipc_register.py <instance_id> first."
        )

    try:
        payload = json.loads(candidate_path.read_text())
        instance_id = payload["instance_id"]
        session_token = payload["session_token"]
    except Exception as exc:  # noqa: BLE001 - surface helpful error
        raise ValueError(f"Malformed session file at {candidate_path}: {exc}") from exc

    return SessionData(instance_id=instance_id, session_token=session_token, raw=payload, path=candidate_path)
