"""
Contract test T011a: IPC Register Command

Test the register command functionality including session file creation,
legacy pointer handling, and responder process management.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import subprocess
import threading
from pathlib import Path
from tests.helpers.cli import run_ipc

# Test broker configuration
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 18876


def test_register_script_creates_legacy_session_file(tmp_path: Path, monkeypatch):
    # Arrange: isolated HOME/USERPROFILE and clean env
    responder_id = "contract-bot"
    monkeypatch.delenv("IPC_SHARED_SECRET", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    # Use a local fake broker to avoid dependency on any external/shared-secret broker
    _run_fake_broker()
    monkeypatch.setenv("IPC_BROKER_HOST", BROKER_HOST)
    monkeypatch.setenv("IPC_BROKER_PORT", str(BROKER_PORT))

    # Act: run the register script directly with Python
    # Note: contract specifies `python tools/ipc_register_with_responder.py <id>`
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ipc_register_with_responder.py"
    res = subprocess.run(
        [sys.executable, str(script), responder_id, "--no-responder"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    # Assert: exit code 0 and legacy session files created in temp home
    assert res.returncode == 0, res.stderr or res.stdout
    legacy = tmp_path / f".ipc-session-{responder_id}"
    assert legacy.exists(), f"expected legacy session file to exist: {legacy}"

    # Optional: if pointer file exists, ensure it mentions the id
    content = legacy.read_text(encoding="utf-8", errors="ignore")
    assert responder_id in content or len(content) == 0

    # And legacy pointer should also be updated unless --no-default is passed
    default_ptr = tmp_path / ".ipc-session"
    assert default_ptr.exists(), "Default session pointer should exist when --no-default not used"


def _run_fake_broker(port=BROKER_PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((BROKER_HOST, port))
    s.listen(1)

    def _serve():
        try:
            conn, _ = s.accept()
            data = conn.recv(65536)
            payload = json.loads(data.decode("utf-8"))
            # minimal register response
            resp = {"status": "ok", "session_token": "test-token", "message": f"Registered {payload.get('instance_id','id')}"}
            conn.send(json.dumps(resp).encode("utf-8"))
            conn.close()
        finally:
            s.close()

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    return t


def test_register_creates_session_and_legacy_pointer(tmp_path: Path, monkeypatch):
    """T011a.1: Register creates session file and updates legacy pointer by default."""
    responder_id = "codex-test"
    monkeypatch.delenv("IPC_SHARED_SECRET", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    # Start fake broker
    _run_fake_broker(BROKER_PORT)
    monkeypatch.setenv("IPC_BROKER_HOST", BROKER_HOST)
    monkeypatch.setenv("IPC_BROKER_PORT", str(BROKER_PORT))

    # Run register command
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ipc_register_with_responder.py"
    result = subprocess.run(
        [sys.executable, str(script), responder_id, "--no-responder"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    # Check exit code 0
    assert result.returncode == 0, result.stdout + result.stderr

    # Check session file created
    session_file = tmp_path / f".ipc-session-{responder_id}"
    assert session_file.exists(), f"Session file should exist: {session_file}"

    # Check legacy pointer updated
    legacy_pointer = tmp_path / ".ipc-session"
    assert legacy_pointer.exists(), "Legacy pointer should exist"


def test_register_no_default_skips_legacy_pointer(tmp_path: Path, monkeypatch):
    """T011a.2: Register with --no-default does not update legacy pointer."""
    responder_id = "alpha"
    monkeypatch.delenv("IPC_SHARED_SECRET", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    # Start fake broker
    _run_fake_broker(BROKER_PORT + 1)
    monkeypatch.setenv("IPC_BROKER_HOST", BROKER_HOST)
    monkeypatch.setenv("IPC_BROKER_PORT", str(BROKER_PORT + 1))

    # Run register command with --no-default
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ipc_register_with_responder.py"
    result = subprocess.run(
        [sys.executable, str(script), responder_id, "--no-responder", "--no-default"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    # Check exit code 0
    assert result.returncode == 0

    # Check session file created
    session_file = tmp_path / f".ipc-session-{responder_id}"
    assert session_file.exists(), f"Session file should exist: {session_file}"

    # Check legacy pointer NOT created
    legacy_pointer = tmp_path / ".ipc-session"
    assert not legacy_pointer.exists(), "Legacy pointer should not exist with --no-default"


def test_register_succeeds_even_if_responder_fails(tmp_path: Path, monkeypatch):
    """T011a.3: Register returns 0 even if responder fails to start, but prints warning."""
    responder_id = "beta"
    monkeypatch.delenv("IPC_SHARED_SECRET", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    # Start fake broker
    _run_fake_broker(BROKER_PORT + 2)
    monkeypatch.setenv("IPC_BROKER_HOST", BROKER_HOST)
    monkeypatch.setenv("IPC_BROKER_PORT", str(BROKER_PORT + 2))

    # Run register command with responder flag (will fail but registration should succeed)
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tools" / "ipc_register_with_responder.py"

    # Set a non-existent responder script to simulate failure
    monkeypatch.setenv("IPC_RESPONDER_SCRIPT", "/nonexistent/script.py")

    result = subprocess.run(
        [sys.executable, str(script), responder_id],  # No --no-responder, so it will try to start
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    # Check exit code 0 (registration succeeds even if responder fails)
    assert result.returncode == 0, "Should return 0 even if responder fails"

    # Check session file created
    session_file = tmp_path / f".ipc-session-{responder_id}"
    assert session_file.exists(), f"Session file should exist: {session_file}"

    # Check that warning was printed (either "warning" or "failed" in output)
    output = result.stdout + result.stderr
    assert "warning" in output.lower() or "failed" in output.lower() or "responder" in output.lower(), \
        "Should print warning about responder failure"
