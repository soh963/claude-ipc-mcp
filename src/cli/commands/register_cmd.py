from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

# MIGRATION: Use local_broker_client (absolute rules)
import local_broker_client as broker_client
from core.project_context import write_session, default_instance_id
from core.logging_utils import with_logging, setup_project_logging


def _initialized(root: Path | None = None) -> bool:
    root = (root or Path.cwd()).resolve()
    return (root / ".ipc").exists()


@with_logging("register")
def run_register(no_default: bool = False, instance_id: str | None = None) -> int:
    """Register this instance with local broker (absolute rules).

    Args:
        no_default: Whether to skip default instance_id from config
        instance_id: Optional instance_id to override config file

    Prints JSON: {"instance_id", "session_token"} on success.
    Returns 0 on success, 12 on failure (to match router conventions).
    """
    # Auto-detect project root (.ipc priority)
    root = broker_client.detect_project_root()

    if not _initialized(root):
        print("error: project not initialized; run 'ipc init'")
        return 12

    # Setup logging
    setup_project_logging(root)

    # Use provided instance_id or read from config
    instance = instance_id if instance_id else default_instance_id(root)

    # Register with local broker (simplified - no TCP auth token needed)
    try:
        resp = broker_client.register(instance)

        if resp.get("status") == "ok":
            session_token = resp.get("session_token", "")

            # Persist session into project state
            write_session(instance, session_token, root)

            print(json.dumps({
                "instance_id": instance,
                "session_token": session_token,
                "mode": "local"
            }))
            return 0
        else:
            error_msg = resp.get("message", "Registration failed")
            print(f"error: {error_msg} (instance={instance})")
            return 12

    except Exception as e:
        print(f"error: failed to register: {e} (instance={instance})")
        return 12
