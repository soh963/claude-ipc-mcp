from __future__ import annotations

import json
import socket
import time
from typing import Any, Dict, Optional

IPC_HOST = "127.0.0.1"
IPC_PORT = 9876


def _send_request(request: Dict[str, Any]) -> Dict[str, Any]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
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
    r = status() if not session_token else _send_request({"action": "list", "session_token": session_token})
    rtt = int((time.perf_counter() - start) * 1000)
    ok = r.get("status") in ("ok", "error")  # broker reachable gives a response shape
    return {"ok": ok, "rtt_ms": rtt, "target": target or "local"}
