#!/usr/bin/env python3
"""Send a message to another instance via IPC."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from typing import Any, Dict

from session_utils import load_session

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876


def build_request(from_id: str, to_id: str, session_token: str, content: str) -> Dict[str, Any]:
    return {
        "action": "send",
        "from_id": from_id,
        "to_id": to_id,
        "message": {"content": content},
        "session_token": session_token,
    }


def send_message(to_id: str, content: str, *, instance_id: str | None = None) -> None:
    session = load_session(instance_id)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((BROKER_HOST, BROKER_PORT))
    except OSError as exc:
        raise SystemExit(
            f"Error: Could not connect to broker at {BROKER_HOST}:{BROKER_PORT} ({exc})."
        )

    try:
        payload = build_request(session.instance_id, to_id, session.session_token, content)
        sock.send(json.dumps(payload).encode("utf-8"))
        response = json.loads(sock.recv(65536).decode("utf-8"))
    finally:
        sock.close()

    if response.get("status") == "ok":
        print(f"Sent to {to_id}: {content}")
    else:
        raise SystemExit(json.dumps(response, indent=2))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a message via the IPC broker.")
    parser.add_argument("to_instance", help="Target instance id (case-sensitive).")
    parser.add_argument("message", nargs=argparse.REMAINDER, help="Message content to send.")
    parser.add_argument(
        "--instance",
        help="Source instance id to use (defaults to the sole or legacy session file).",
    )
    args = parser.parse_args(argv)
    if not args.message:
        parser.error("Message content is required.")
    args.message = " ".join(args.message)
    return args


if __name__ == "__main__":
    cli_args = parse_args(sys.argv[1:])
    send_message(cli_args.to_instance, cli_args.message, instance_id=cli_args.instance)
