from __future__ import annotations

import json
from pathlib import Path
from ._shared import ensure_broker, get_cli_version, read_project_id
from core.project_context import read_session
from core import broker_client
from core.logging_utils import with_logging, setup_project_logging


@with_logging("status")
def run_status(verbose: bool = False) -> int:
    # Setup logging if project initialized
    project_root = Path.cwd()
    if (project_root / ".ipc").exists():
        setup_project_logging(project_root)

    running = False
    connections = 0
    current_version = get_cli_version()
    status_check_method = None

    # Multi-layer broker health check (강력한 다단계 체크)
    # Layer 1: Try ping first (faster and more reliable)
    last_ping_ms = None
    ping_success = False
    try:
        ping_result = broker_client.ping()
        if ping_result.get("ok"):
            ping_success = True
            last_ping_ms = ping_result.get("rtt_ms")
            status_check_method = "ping"
    except Exception:
        pass

    # Layer 2: Try status API (may timeout but gives instance count)
    try:
        ensure_broker()
        resp = broker_client.status()
        if resp.get("status") == "ok":
            running = True
            status_check_method = "status_api"
            connections = (
                len(resp.get("instances", [])) if isinstance(resp.get("instances"), list) else 0
            )
    except Exception:
        # If status fails but ping succeeded, broker is still running
        if ping_success:
            running = True
            status_check_method = "ping_fallback"

    # Layer 3: Socket-level probe (최후 수단)
    if not running and not ping_success:
        try:
            if broker_client.is_broker_available(timeout_s=1.0):
                running = True
                status_check_method = "socket_probe"
        except Exception:
            pass

    project_id = read_project_id(Path.cwd())

    # Base status payload
    data = {
        "broker": {"running": running, "version": current_version, "compatible": True},
        "connections": connections,
        "last_ping_ms": last_ping_ms,
    }

    # Initialization indicator and project_id handling
    initialized = project_id is not None
    data["initialized"] = bool(initialized)
    if initialized:
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
        try:
            if hasattr(broker_client, "IPC_PORT"):
                data["broker"]["port"] = int(getattr(broker_client, "IPC_PORT"))
        except Exception:
            pass
        # Add status check method for debugging
        if status_check_method:
            data["broker"]["status_check_method"] = status_check_method

    print(json.dumps(data))
    return 0
