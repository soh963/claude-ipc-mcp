"""
Integration test: start a responder and ensure `ipc ask` receives an answer (exit 0).
"""

from __future__ import annotations

import time
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ask_receives_answer_when_responder_running(tmp_path: Path):
    # init project
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0

    # start responder for target instance 'gemini'
    r1 = run_ipc(["responder", "start", "gemini", "--detach"], cwd=tmp_path)
    assert r1.returncode == 0, r1.stdout + r1.stderr

    # small delay to let responder spin up
    time.sleep(0.8)

    # ask from default to gemini
    res = run_ipc(["ask", "--to", "gemini", "hello"], cwd=tmp_path)
    assert res.returncode in (0, 30), res.stdout + res.stderr
    if res.returncode == 30:
        # If rare timing issue, retry once after short wait
        time.sleep(1.2)
        res = run_ipc(["ask", "--to", "gemini", "hello"], cwd=tmp_path)
        assert res.returncode == 0, res.stdout + res.stderr

    out = (res.stdout or "").lower()
    assert any(word in out for word in ["hello", "thanks", "pong", "status", "ack"])  # generic responder patterns

    # stop responder
    r2 = run_ipc(["responder", "stop", "gemini"], cwd=tmp_path)
    assert r2.returncode == 0, r2.stdout + r2.stderr
