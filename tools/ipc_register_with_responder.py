#!/usr/bin/env python3
"""Register an IPC instance and optionally launch an auto-responder.

This combines tools/ipc_register.py with a convenience flag to start a
background responder process for the given instance after successful
registration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

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


def register_instance(instance_id: str, *, set_default: bool = True) -> Tuple[bool, str, str | None]:
    """Register an instance with the broker and persist the session.

    Returns (success, message, session_path or None on failure)
    """
    shared_secret = os.environ.get("IPC_SHARED_SECRET", "")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((BROKER_HOST, BROKER_PORT))
    except OSError as exc:
        return False, f"Cannot connect to broker at {BROKER_HOST}:{BROKER_PORT} ({exc}).", None

    try:
        payload = build_request(instance_id, shared_secret)
        sock.send(json.dumps(payload).encode("utf-8"))
        response = json.loads(sock.recv(65536).decode("utf-8"))
    finally:
        sock.close()

    if response.get("status") != "ok" or "session_token" not in response:
        # Surface the broker's response for diagnostics
        return False, json.dumps(response, indent=2), None

    session_payload = {
        "instance_id": instance_id,
        "session_token": response["session_token"],
    }

    session_path = save_session(instance_id, session_payload, set_default=set_default)
    try:
        os.chmod(session_path, 0o600)
        if set_default:
            os.chmod(session_path.parent / ".ipc-session", 0o600)
    except Exception:
        # On Windows, chmod is best-effort and may not apply. Ignore.
        pass

    message = response.get("message", f"Registered {instance_id}")
    return True, message, str(session_path)


def start_auto_responder(instance_id: str) -> bool:
    """Launch the simple auto-responder script for the instance in background."""
    print(f"🤖 Starting auto-responder for {instance_id}...")

    # Prefer simple_auto_responder.py; fall back to auto_responder.py for older setups
    responder_script = Path(__file__).parent / "simple_auto_responder.py"
    if not responder_script.exists():
        alt = Path(__file__).parent / "auto_responder.py"
        if alt.exists():
            responder_script = alt

    if not responder_script.exists():
        print(f"❌ Auto-responder script not found: {responder_script}")
        return False

    try:
        if os.name == "nt":
            # Launch without opening a new console window; avoid brittle PowerShell quoting
            creation_flags = 0
            creation_flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
            creation_flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

            subprocess.Popen(
                [sys.executable, str(responder_script), instance_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            time.sleep(2)
            return True

        # POSIX
        proc = subprocess.Popen(
            [sys.executable, str(responder_script), instance_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(2)
        return proc.poll() is None
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error starting auto-responder: {exc}")
        return False


def check_existing_responder(instance_id: str) -> bool:
    """Best-effort check for an already running auto-responder."""
    try:
        if os.name == "nt":
            # Use window title heuristic from batch scripts if available
            result = subprocess.run(
                ["tasklist"],
                capture_output=True,
                text=True,
            )
            return "python.exe" in result.stdout
        result = subprocess.run(
            f"ps aux | grep 'auto_responder.py {instance_id}' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register an IPC instance and optionally start an auto-responder.")
    parser.add_argument("instance_id", help="Unique name for this AI instance (e.g., codex).")
    parser.add_argument(
        "--no-responder",
        action="store_true",
        help="Skip launching the auto-responder after registration.",
    )
    parser.add_argument(
        "--no-default",
        action="store_true",
        help="Do not update the legacy ~/.ipc-session file.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    print("\n" + "=" * 50)
    print("  IPC Registration with Auto-Responder")
    print("=" * 50)
    print(f"Instance: {args.instance_id}")
    print(f"Auto-responder: {'Disabled' if args.no_responder else 'Enabled'}")
    print()

    print("[1/2] Registering instance...")
    success, message, session_path = register_instance(args.instance_id, set_default=not args.no_default)
    if not success:
        print(f"❌ Registration failed: {message}")
        return 1

    print(f"✅ {message}")
    if session_path:
        print(f"📁 Session stored at {session_path}")

    if args.no_responder or args.instance_id.lower() == "claude":
        if args.instance_id.lower() == "claude":
            print("\n[2/2] Skipping auto-responder (Claude is typically controlled manually)")
        else:
            print("\n[2/2] Skipping auto-responder (--no-responder flag)")
        print("\n✅ Complete! Instance is ready.")
    else:
        print("\n[2/2] Starting auto-responder...")
        if check_existing_responder(args.instance_id):
            print(f"⚠️ Auto-responder may already be running for {args.instance_id}")
        elif start_auto_responder(args.instance_id):
            print("✅ Auto-responder started successfully")
        else:
            print("⚠️ Instance registered, but auto-responder failed to start")

    print("\n" + "=" * 50)
    print("Ready to send/receive messages!")
    print(
        "  Send: python tools/ipc_send.py --instance "
        f"{args.instance_id} <to_id> \"message\""
    )
    print(
        "  Check: python tools/ipc_check.py --instance "
        f"{args.instance_id}"
    )
    print("=" * 50 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
