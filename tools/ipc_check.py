#!/usr/bin/env python3
"""Check for messages from the IPC server."""
from __future__ import annotations

import argparse
import json
import socket
import sys

from session_utils import load_session

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876


def check_messages(instance_id: str | None = None) -> None:
    session = load_session(instance_id)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((BROKER_HOST, BROKER_PORT))
    except OSError as exc:
        raise SystemExit(f"Error: Could not connect to broker at {BROKER_HOST}:{BROKER_PORT} ({exc}).")

    try:
        request = {
            "action": "check",
            "instance_id": session.instance_id,
            "session_token": session.session_token,
        }
        sock.send(json.dumps(request).encode("utf-8"))
        response = json.loads(sock.recv(65536).decode("utf-8"))
    finally:
        sock.close()

    if response.get("status") != "ok":
        raise SystemExit(json.dumps(response, indent=2))

    messages = response.get("messages", [])
    if not messages:
        print("No new messages")
        return

    print("New messages:")
    print("-" * 50)
    for msg in messages:
        print(f"From: {msg['from']}")
        print(f"Time: {msg['timestamp']}")
        print(f"Content: {msg['message']['content']}")
        if msg['message'].get('data'):
            print(f"Data: {json.dumps(msg['message']['data'], indent=2)}")
        print("-" * 50)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check for messages from the IPC broker.")
    parser.add_argument(
        "--instance",
        help="Instance id whose inbox should be checked (defaults to the sole or legacy session file).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    cli_args = parse_args(sys.argv[1:])
    check_messages(instance_id=cli_args.instance)
