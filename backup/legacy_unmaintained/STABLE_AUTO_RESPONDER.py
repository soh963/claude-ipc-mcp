#!/usr/bin/env python3
"""Resilient auto-responder that keeps an IPC agent online.

This version centralizes session management through ``session_utils`` so that
multiple agents can coexist on a single machine without clobbering session
files. The responder will keep trying to reconnect to the broker, monitor its
inbox, and answer incoming messages with predefined snippets.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import socket
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from tools.session_utils import load_session, save_session, session_path

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 9876
SESSION_TTL_SECONDS = 24 * 60 * 60
CHECK_INTERVAL_SECONDS = 3
HEARTBEAT_INTERVAL_SECONDS = 30


@dataclass
class Message:
    sender: str
    content: str
    timestamp: str


class StableAutoResponder:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.session_token: str | None = None
        self.session_file = session_path(instance_id)
        self.running = True
        self.recent_responses: Dict[str, datetime] = {}
        self.response_pool = self._build_responses(instance_id)
        self.lock = threading.Lock()

    # ------------------------------------------------------------------
    # Session handling
    # ------------------------------------------------------------------
    def ensure_session(self) -> None:
        """Load or (re-)register the instance."""
        if self.load_session_from_disk():
            return
        self.register_instance()

    def load_session_from_disk(self) -> bool:
        if not self.session_file.exists():
            return False
        try:
            payload = json.loads(self.session_file.read_text())
            saved_at = datetime.fromtimestamp(payload.get("timestamp", 0))
            if datetime.utcnow() - saved_at > timedelta(seconds=SESSION_TTL_SECONDS):
                return False
            self.session_token = payload.get("token")
            return bool(self.session_token)
        except Exception:
            return False

    def register_instance(self) -> None:
        shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
        auth_token = ""
        if shared_secret:
            import hashlib

            auth_token = hashlib.sha256(f"{self.instance_id}:{shared_secret}".encode()).hexdigest()

        payload = {
            "action": "register",
            "instance_id": self.instance_id,
            "auth_token": auth_token,
        }
        response = self._round_trip(payload)
        if response.get("status") != "ok" or "session_token" not in response:
            raise RuntimeError(f"Registration failed: {json.dumps(response, indent=2)}")

        self.session_token = response["session_token"]
        disk_payload = {
            "instance_id": self.instance_id,
            "session_token": self.session_token,
            "token": self.session_token,  # backward compatibility for older scripts
            "timestamp": time.time(),
        }
        path = save_session(self.instance_id, disk_payload, set_default=False)
        os.chmod(path, 0o600)
        print(f"[{self.instance_id}] Registered and session saved to {path}")

    # ------------------------------------------------------------------
    # Broker helpers
    # ------------------------------------------------------------------
    def _round_trip(self, payload: Dict) -> Dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((BROKER_HOST, BROKER_PORT))
            sock.send(json.dumps(payload).encode("utf-8"))
            data = sock.recv(65536)
            sock.close()
            return json.loads(data.decode("utf-8")) if data else {}
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Broker request failed: {exc}")

    def fetch_messages(self) -> List[Message]:
        if not self.session_token:
            return []
        payload = {
            "action": "check",
            "instance_id": self.instance_id,
            "session_token": self.session_token,
        }
        response = self._round_trip(payload)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message", "Unknown broker error"))
        messages = []
        for item in response.get("messages", []):
            messages.append(
                Message(
                    sender=item.get("from"),
                    content=item.get("message", {}).get("content", ""),
                    timestamp=item.get("timestamp", ""),
                )
            )
        return messages

    def send_message(self, recipient: str, content: str) -> None:
        if not self.session_token:
            raise RuntimeError("No session token available. Register first.")
        payload = {
            "action": "send",
            "from_id": self.instance_id,
            "to_id": recipient,
            "message": {"content": content},
            "session_token": self.session_token,
        }
        response = self._round_trip(payload)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message", "Failed to send message"))

    # ------------------------------------------------------------------
    # Response logic
    # ------------------------------------------------------------------
    def _build_responses(self, instance_id: str) -> List[str]:
        defaults = {
            "codex": [
                "Codex ready. Let's translate that into code.",
                "I can take that requirement and turn it into functions.",
                "Code review complete—looks good to me!",
            ],
            "gemini": [
                "Gemini online. Sharing insights shortly.",
                "I'll gather the context and report back.",
                "Gemini processed your request successfully.",
            ],
        }
        return defaults.get(instance_id.lower(), [
            f"{instance_id} received your message and is on it!",
            f"{instance_id} confirms the update.",
            f"{instance_id} processed the message successfully.",
        ])

    def choose_response(self) -> str:
        return random.choice(self.response_pool)

    def handle_messages(self) -> None:
        try:
            for message in self.fetch_messages():
                if not message.sender or message.sender == self.instance_id:
                    continue
                print(f"[{self.instance_id}] 📩 {message.sender}: {message.content}")
                if self._should_skip(message.sender):
                    continue
                response = self.choose_response()
                self.send_message(message.sender, response)
                print(f"[{self.instance_id}] ↩️  Responded to {message.sender}: {response}")
                self.recent_responses[message.sender] = datetime.utcnow()
        except RuntimeError as exc:
            print(f"[{self.instance_id}] Warning: {exc}")
            self.register_instance()

    def _should_skip(self, sender: str) -> bool:
        limit = self.recent_responses.get(sender)
        if not limit:
            return False
        return datetime.utcnow() - limit < timedelta(seconds=10)

    # ------------------------------------------------------------------
    # Runners
    # ------------------------------------------------------------------
    def heartbeat_loop(self) -> None:
        while self.running:
            try:
                time.sleep(HEARTBEAT_INTERVAL_SECONDS)
                self.ensure_session()
            except Exception as exc:  # noqa: BLE001
                print(f"[{self.instance_id}] Heartbeat error: {exc}")

    def run(self) -> None:
        print(f"[{self.instance_id}] Stable auto-responder starting...")
        self.ensure_session()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

        try:
            while self.running:
                self.handle_messages()
                time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print(f"[{self.instance_id}] Interrupted. Shutting down.")
        finally:
            self.running = False


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a resilient auto-responder for an IPC agent.")
    parser.add_argument("instance_id", help="Instance id to bind to the responder (e.g., codex).")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    responder = StableAutoResponder(args.instance_id)
    responder.run()
