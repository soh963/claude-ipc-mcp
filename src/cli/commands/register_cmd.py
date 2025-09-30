from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from ._shared import ensure_broker
from core.project_context import write_session, default_instance_id
from core import broker_client
from core.logging_utils import with_logging, setup_project_logging


def _initialized(root: Path | None = None) -> bool:
    root = (root or Path.cwd()).resolve()
    return (root / ".ipc").exists()


@with_logging("register")
def run_register(no_default: bool = False) -> int:
    """Register this project instance with the broker and persist session.

    Prints JSON: {"instance_id", "session_token"} on success.
    Returns 0 on success, 12 on failure (to match router conventions).
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

    instance = default_instance_id(root)

    # Derive auth token from shared secret
    shared = os.environ.get("IPC_SHARED_SECRET", "")
    auth_token: str | None = None
    if shared:
        auth_token = hashlib.sha256(f"{instance}:{shared}".encode()).hexdigest()

    # Attempt register with short retries (up to ~2.5s)
    import time as _t

    session_token: str | None = None
    last_err: str | None = None
    for _ in range(50):
        try:
            resp = broker_client.register(instance, auth_token=auth_token)
            if resp.get("status") == "ok" and resp.get("session_token"):
                session_token = resp["session_token"]
                break
            last_err = resp.get("message")
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        _t.sleep(0.05)

    if not session_token:
        diag_tok = (auth_token[:8] + "…") if auth_token else None
        if last_err:
            print(f"error: failed to register: {last_err} (instance={instance} token={diag_tok})")
        else:
            print(f"error: failed to register (instance={instance} token={diag_tok})")
        return 12

    # Persist session into project state
    write_session(instance, session_token, root)

    # We don't manage legacy HOME pointers here; that is handled by tools/ipc_register_with_responder.py

    print(json.dumps({"instance_id": instance, "session_token": session_token}))
    return 0
