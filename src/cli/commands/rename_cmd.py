from __future__ import annotations

import json
from pathlib import Path

from ._shared import ensure_broker
from core.project_context import read_session, write_session
from core import broker_client
from core.logging_utils import with_logging, setup_project_logging


def _initialized(root: Path | None = None) -> bool:
    root = (root or Path.cwd()).resolve()
    return (root / ".ipc").exists()


@with_logging("rename")
def run_rename(old_name: str, new_name: str) -> int:
    """Rename an instance (rate limited to once per hour).

    Args:
        old_name: Current instance ID
        new_name: New instance ID

    Prints result message on success/failure.
    Returns 0 on success, 12 on failure.
    """
    root = Path.cwd()
    if not _initialized(root):
        print("error: project not initialized; run 'ipc init'")
        return 12

    # Setup logging and ensure broker
    setup_project_logging(root)
    try:
        ensure_broker()
    except Exception:
        pass

    # Read current session
    session = read_session(root)
    if not session or session.instance_id != old_name:
        print(f"error: not registered as '{old_name}' in this project")
        return 12

    session_token = session.session_token
    if not session_token:
        print("error: no valid session token found")
        return 12

    # Attempt rename via broker
    try:
        resp = broker_client._send_request({
            "action": "rename",
            "old_id": old_name,
            "new_id": new_name,
            "session_token": session_token,
        })

        if resp.get("status") == "ok":
            # Update local session with new instance_id
            write_session(new_name, session_token, root)
            print(f"renamed {old_name} → {new_name}")
            return 0
        else:
            err_msg = resp.get("message", "unknown error")
            print(f"error: {err_msg}")
            return 12

    except Exception as e:
        print(f"error: failed to rename: {e}")
        return 12
