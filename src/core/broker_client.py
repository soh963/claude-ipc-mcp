from __future__ import annotations

import json
import socket
import time
import os
from pathlib import Path
from typing import Any, Dict, Optional

def _get_project_config() -> tuple[str, int]:
    """Get broker host and port from project config or environment variables."""
    # 1. Try to read from project-local .ipc/state/project.json
    try:
        from core.project_local import detect_project_root
        project_root = detect_project_root()
        project_json = project_root / ".ipc" / "state" / "project.json"

        if project_json.exists():
            config = json.loads(project_json.read_text(encoding="utf-8"))
            host = config.get("broker_host", "127.0.0.1")
            port = config.get("broker_port", 9876)
            return host, int(port)
    except Exception:
        pass

    # 2. Fallback to environment variables
    host = os.getenv("IPC_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("IPC_GLOBAL_PORT", os.getenv("IPC_PORT", "9876")))
    except ValueError:
        port = 9876

    return host, port

# Get project-specific or global configuration
IPC_HOST, IPC_PORT = _get_project_config()


def _send_request(request: Dict[str, Any]) -> Dict[str, Any]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Get timeout from environment variable or use default
        timeout = float(os.getenv("IPC_TIMEOUT", "30.0"))  # Increased default to 30 seconds
        s.settimeout(timeout)
        s.connect((IPC_HOST, IPC_PORT))
        s.send(json.dumps(request).encode("utf-8"))
        resp = s.recv(65536).decode("utf-8")
        s.close()
        return json.loads(resp)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def status() -> Dict[str, Any]:
    return _send_request({"action": "list"})


def register(instance_id: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
    req = {"action": "register", "instance_id": instance_id}
    if auth_token:
        req["auth_token"] = auth_token
    return _send_request(req)


def send(session_token: str, from_id: str, to_id: str, content: str) -> Dict[str, Any]:
    return _send_request(
        {
            "action": "send",
            "session_token": session_token,
            "from_id": from_id,
            "to_id": to_id,
            "message": {"content": content},
        }
    )


def ping(session_token: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
    # No explicit ping action: synthesize via small request and measure RTT
    start = time.perf_counter()
    r = (
        status()
        if not session_token
        else _send_request({"action": "list", "session_token": session_token})
    )
    rtt = int((time.perf_counter() - start) * 1000)
    ok = r.get("status") in ("ok", "error")  # broker reachable gives a response shape
    return {"ok": ok, "rtt_ms": rtt, "target": target or "local"}


# --- T029: Broker detection and auto-start helpers ---


def is_broker_available(timeout_s: float = 0.5) -> bool:
    """Return True if broker responds to a status request within timeout.

    Non-throwing, conservative check: only returns True when we get a valid-shaped
    response with status in ("ok", "error").
    """
    try:
        # quick socket-level probe to avoid long hangs
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout_s)
        s.connect((IPC_HOST, IPC_PORT))
        s.close()
    except Exception:
        return False
    try:
        r = status()
        return r.get("status") in ("ok", "error")
    except Exception:
        return False


def ensure_broker_running(max_wait_s: float = 1.0) -> bool:
    """Ensure a broker is running locally.

    Best-effort: tries import-based in-process start (claude_ipc_server) and then polls
    status up to max_wait_s. Returns True if reachable, else False.
    """
    if is_broker_available(0.2):
        return True
    # Try to start embedded broker
    try:
        import importlib

        importlib.import_module("claude_ipc_server")
    except Exception:
        # Ignore; we'll just fall back to polling
        pass
    # Poll for readiness
    deadline = time.perf_counter() + max_wait_s
    while time.perf_counter() < deadline:
        if is_broker_available(0.2):
            return True
        time.sleep(0.05)
    return is_broker_available(0.2)
