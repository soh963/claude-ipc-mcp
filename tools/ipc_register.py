#!/usr/bin/env python3
"""Register an instance with the IPC server."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
from typing import Any, Dict

from session_utils import save_session

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876


def build_request(instance_id: str, shared_secret: str | None) -> Dict[str, Any]:
    auth_token = ""
    if shared_secret:
        auth_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()

    return {
        "action": "register",
        "instance_id": instance_id,
        "auth_token": auth_token,
    }


def register_instance(instance_id: str, *, set_default: bool = True) -> None:
    shared_secret = os.environ.get("IPC_SHARED_SECRET", "")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((BROKER_HOST, BROKER_PORT))
    except OSError as exc:
        raise SystemExit(
            f"Error: Could not connect to broker at {BROKER_HOST}:{BROKER_PORT} ({exc})."
        )

    try:
        payload = build_request(instance_id, shared_secret)
        sock.send(json.dumps(payload).encode("utf-8"))
        response = json.loads(sock.recv(65536).decode("utf-8"))
    finally:
        sock.close()

    if response.get("status") != "ok" or "session_token" not in response:
        raise SystemExit(json.dumps(response, indent=2))

    session_payload = {
        "instance_id": instance_id,
        "session_token": response["session_token"],
    }

    session_path = save_session(instance_id, session_payload, set_default=set_default)
    os.chmod(session_path, 0o600)
    if set_default:
        os.chmod(session_path.parent / ".ipc-session", 0o600)

    print(f"Registered as {instance_id}")
    print(f"Session stored at: {session_path}")
    if not set_default:
        print("(Use --set-default to refresh ~/.ipc-session for legacy scripts.)")
    if "message" in response:
        print(response["message"])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register an instance with the IPC broker.")
    parser.add_argument("instance_id", help="Unique name for this AI instance (e.g., codex).")
    parser.add_argument(
        "--no-default",
        action="store_true",
        help="Do not update the legacy ~/.ipc-session file (useful when running multiple agents).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    register_instance(args.instance_id, set_default=not args.no_default)
