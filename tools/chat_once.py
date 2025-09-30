#!/usr/bin/env python3
"""Send a single IPC message and wait for the recipient's reply."""
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from session_utils import load_session
from ipc_register import register_instance

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876
DEFAULT_TIMEOUT = 15
POLL_INTERVAL = 0.8

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).parent
PYTHON = sys.executable


def ensure_broker() -> None:
    subprocess.run(
        [PYTHON, str(TOOLS_DIR / "start_broker.py")],
        cwd=str(REPO_ROOT),
        check=True,
        text=True,
    )


def ensure_session(instance_id: str) -> str:
    try:
        session = load_session(instance_id)
        return session.session_token
    except FileNotFoundError:
        register_instance(instance_id, set_default=False)
        session = load_session(instance_id)
        return session.session_token


def call_broker(payload: dict[str, object]) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((BROKER_HOST, BROKER_PORT))
        sock.send(json.dumps(payload).encode("utf-8"))
        data = sock.recv(65536)
    if not data:
        return {}
    return json.loads(data.decode("utf-8"))


def send_message(from_id: str, session_token: str, to_id: str, content: str) -> None:
    response = call_broker(
        {
            "action": "send",
            "from_id": from_id,
            "to_id": to_id,
            "message": {"content": content},
            "session_token": session_token,
        }
    )
    if response.get("status") != "ok":
        raise RuntimeError(response.get("message", "Failed to send message"))


def check_messages(instance_id: str, session_token: str) -> list[dict[str, object]]:
    response = call_broker(
        {
            "action": "check",
            "instance_id": instance_id,
            "session_token": session_token,
        }
    )
    if response.get("status") != "ok":
        raise RuntimeError(response.get("message", "Failed to check messages"))
    return response.get("messages", [])


def launch_responder(instance_id: str, monitor: bool) -> Optional[subprocess.Popen]:
    proc = subprocess.Popen(
        [PYTHON, str(TOOLS_DIR / "simple_auto_responder.py"), instance_id],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE if monitor else subprocess.DEVNULL,
        stderr=subprocess.STDOUT if monitor else subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    if monitor and proc.stdout is not None:
        threading.Thread(
            target=_stream_output,
            args=(proc.stdout, instance_id),
            daemon=True,
        ).start()
    return proc


def _stream_output(stream, label: str) -> None:
    for line in stream:
        print(f"[{label}] {line.rstrip()}")


def stop_process(proc: Optional[subprocess.Popen]) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def wait_for_reply(
    sender: str, token: str, expected_from: str, baseline: datetime, timeout: int
) -> Optional[dict[str, object]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        messages = check_messages(sender, token)
        for message in messages:
            if message.get("from") != expected_from:
                continue
            timestamp = message.get("timestamp")
            if timestamp:
                try:
                    msg_time = datetime.fromisoformat(timestamp)
                    if msg_time < baseline:
                        continue
                except ValueError:
                    pass
            return message
        time.sleep(POLL_INTERVAL)
    return None


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a message and wait for the reply.")
    parser.add_argument("sender", help="Instance id to send from (e.g., codex)")
    parser.add_argument("receiver", help="Instance id to send to (e.g., gemini)")
    parser.add_argument("message", nargs="+", help="Message to deliver")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Seconds to wait for a reply (default: 15)",
    )
    parser.add_argument(
        "--auto-responder",
        action="store_true",
        help="Temporarily launch a responder for the receiver if not already running.",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Stream the receiver auto-responder output while waiting.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> None:
    args = parse_args(argv)
    message_text = " ".join(args.message)

    ensure_broker()
    sender_token = ensure_session(args.sender)
    ensure_session(args.receiver)

    responder_proc: Optional[subprocess.Popen] = None
    if args.auto_responder:
        responder_proc = launch_responder(args.receiver, args.monitor)
        time.sleep(1.0)
        if responder_proc and responder_proc.poll() is not None:
            print(
                f"⚠️ Auto-responder for {args.receiver} exited immediately. Continuing without it."
            )
            responder_proc = None

    baseline = datetime.now()
    send_message(args.sender, sender_token, args.receiver, message_text)
    print(f"✅ Sent '{message_text}' from {args.sender} to {args.receiver}")

    try:
        reply = wait_for_reply(args.sender, sender_token, args.receiver, baseline, args.timeout)
        if reply:
            content = reply.get("message", {}).get("content", "")
            print(f"💬 Reply from {args.receiver}: {content}")
        else:
            print(f"⌛ Timeout: no reply from {args.receiver} within {args.timeout} seconds")
    finally:
        if args.auto_responder:
            stop_process(responder_proc)


if __name__ == "__main__":
    main(sys.argv[1:])
