#!/usr/bin/env python3
"""Register an IPC instance and optionally launch an auto-responder."""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

from session_utils import save_session

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876


def register_instance(instance_id: str, *, set_default: bool = True) -> Tuple[bool, str | None, str | None]:
    """Register the instance and persist the session file."""
    shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
    auth_token = ""
    if shared_secret:
        import hashlib

        auth_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((BROKER_HOST, BROKER_PORT))
    except OSError as exc:
        return False, None, f"Cannot connect to broker at {BROKER_HOST}:{BROKER_PORT} ({exc})."

    try:
        payload = {
            "action": "register",
            "instance_id": instance_id,
            "auth_token": auth_token,
        }
        sock.send(json.dumps(payload).encode("utf-8"))
        response = json.loads(sock.recv(65536).decode("utf-8"))
    finally:
        sock.close()

    if response.get("status") != "ok" or "session_token" not in response:
        return False, None, json.dumps(response, indent=2)

    session_payload = {
        "instance_id": instance_id,
        "session_token": response["session_token"],
    }

    session_path = save_session(instance_id, session_payload, set_default=set_default)
    os.chmod(session_path, 0o600)
    if set_default:
        os.chmod(session_path.parent / ".ipc-session", 0o600)

    message = response.get("message", f"Registered {instance_id}")
    return True, message, str(session_path)


def start_auto_responder(instance_id: str) -> bool:
    """Launch the simple auto-responder script for the instance."""
    print(f"🤖 Starting auto-responder for {instance_id}...")
    responder_script = Path(__file__).parent / "simple_auto_responder.py"
    if not responder_script.exists():
        print(f"❌ Auto-responder script not found: {responder_script}")
        return False

    try:
        if os.name == "nt":
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Start-Process -WindowStyle Minimized -FilePath '"
                    f"{sys.executable}' -ArgumentList '"\"{responder_script}\" {instance_id}'"
                ),
            ]
            subprocess.Popen(cmd, shell=False)
            time.sleep(3)
            return check_existing_responder(instance_id)
        proc = subprocess.Popen(
            [sys.executable, str(responder_script), instance_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        if proc.poll() is None:
            return True
        print("❌ Auto-responder exited unexpectedly")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error starting auto-responder: {exc}")
        return False


def check_existing_responder(instance_id: str) -> bool:
    """Best-effort check for an already running auto-responder."""
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"WINDOWTITLE eq Auto-Responder: {instance_id}*"],
                capture_output=True,
                text=True,
            )
            return "python.exe" in result.stdout
        result = subprocess.run(
            f"ps aux | grep 'simple_auto_responder.py {instance_id}' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def parse_args(argv: list[str]) -> argparse.Namespace:
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
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
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
        raise SystemExit(1)

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
            print(f"⚠️ Auto-responder already running for {args.instance_id}")
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


if __name__ == "__main__":
    main(sys.argv[1:])
