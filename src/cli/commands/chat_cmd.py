"""IPC Chat Command Implementation

Task T026: Implements the `ipc chat` command for sending messages to recipients.

Requirements:
- Accept parameters: `--to <recipient>` and message text
- Send message to recipient via broker
- Generate and display correlation ID (format: corr-XXXXX)
- Show acknowledgment (use one of: "ack", "acknowledged", "sent", "delivered", "queued")
- Output format: "to=<recipient> correlation=<id> <acknowledgment>"
- Exit code 0 on success
- Exit code 1 on failure (missing --to parameter, broker offline, etc.)
- Check for project initialization first (fail if not initialized)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

# MIGRATION: Use local_broker_client (absolute rules)
import local_broker_client as broker_client
from core.project_context import read_session, write_session, default_instance_id
from core.logging_utils import with_logging, setup_project_logging


def check_project_initialized(project_root: Optional[Path] = None) -> bool:
    """Check if the project is properly initialized with .ipc structure."""
    if project_root is None:
        project_root = Path.cwd()

    project_root = project_root.resolve()
    ipc_root = project_root / ".ipc"

    # Check if .ipc directory exists (minimal requirement)
    return ipc_root.exists()


def generate_correlation_id(message: str) -> str:
    """Generate a correlation ID in the format corr-XXXXX."""
    # Use hash of message to generate consistent but pseudo-random correlation ID
    correlation_number = abs(hash(message + str(time.time()))) % 100000
    return f"corr-{correlation_number:05d}"


def ensure_session() -> bool:
    """Ensure we have a valid session, register if needed (local broker mode)."""
    sess = read_session()
    if sess:
        return True

    # Try to auto-register with local broker
    if not (default_instance_id and write_session):
        return False

    try:
        project_root = broker_client.detect_project_root()
        instance = default_instance_id(project_root)

        # Register with local broker (simplified - no TCP auth)
        resp = broker_client.register(instance)

        if resp.get("status") == "ok" and resp.get("session_token"):
            write_session(instance, resp["session_token"], project_root)
            return True

        return False
    except Exception:
        return False


@with_logging("chat")
def run_chat(target: str, message: str) -> int:
    """Run the chat command (local broker mode - absolute rules).

    Args:
        target: Recipient of the message (required)
        message: Message content to send

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Check required parameters
    if not target:
        print("error: --to is required", file=sys.stderr)
        return 1

    # Auto-detect project root
    project_root = broker_client.detect_project_root()

    # Check if project is initialized
    if not check_project_initialized(project_root):
        print("error: project not initialized; run 'ipc init'", file=sys.stderr)
        return 1

    # Setup logging
    setup_project_logging(project_root)

    # Generate correlation ID
    correlation_id = generate_correlation_id(message)

    try:
        # Ensure we have a valid session
        if not ensure_session():
            print("error: session not initialized; run 'ipc register'", file=sys.stderr)
            return 1

        # Get session and send message
        sess = read_session()
        if not sess:
            print("error: session not initialized; run 'ipc register'", file=sys.stderr)
            return 1

        # Send message via local broker
        resp = broker_client.send_message(sess.session_token, sess.instance_id, target, message)

        if resp.get("status") == "ok":
            ack = "sent" if message else "ack"
            print(f"to={target} correlation={correlation_id} {ack}")
            return 0
        else:
            error_msg = resp.get("message", "unknown error")
            print(f"error: send failed - {error_msg}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
