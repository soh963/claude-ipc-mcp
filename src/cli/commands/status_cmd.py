from __future__ import annotations

import json
from pathlib import Path
from ._shared import get_cli_version, read_project_id
from core.project_context import read_session
# MIGRATION: Use local_broker_client (absolute rules)
import local_broker_client as broker_client
from core.logging_utils import with_logging, setup_project_logging


@with_logging("status")
def run_status(verbose: bool = False) -> int:
    """Check local broker status (absolute rules - .ipc folder priority)."""
    # Auto-detect project root (.ipc priority)
    project_root = broker_client.detect_project_root()

    if (project_root / ".ipc").exists():
        setup_project_logging(project_root)

    # Check local broker status
    running = broker_client.is_broker_running(project_root)
    current_version = get_cli_version()

    # Get broker info
    broker_info = broker_client.get_project_info()

    project_id = read_project_id(project_root)

    # Base status payload (local broker mode)
    data = {
        "broker": {
            "running": running,
            "version": current_version,
            "mode": "local",  # Unix socket or Named Pipe
            "project_root": str(project_root),
        },
        "initialized": (project_root / ".ipc").exists(),
    }

    if project_id:
        data["project_id"] = project_id

    if verbose:
        try:
            import os as _os
            secret_cfg = bool(_os.environ.get("IPC_SHARED_SECRET"))
        except Exception:
            secret_cfg = False

        sess = read_session()
        data["auth"] = {"shared_secret_configured": secret_cfg}
        data["session"] = {"instance_id": sess.instance_id} if sess else None
        data["broker"].update(broker_info)

    print(json.dumps(data))
    return 0
