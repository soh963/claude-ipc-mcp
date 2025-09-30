"""
Contract tests for `ipc ask` command.
Focus on ack/correlation output and timeout behavior without requiring a real responder.
"""

from __future__ import annotations

import re
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_ask_requires_to_and_prompt(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0

    # Missing --to
    r1 = run_ipc(["ask", "What's up?"], cwd=tmp_path)
    assert r1.returncode != 0
    msg = (r1.stderr or r1.stdout or "").lower()
    assert any(k in msg for k in ["--to", "required", "target"])  # error mentions target


def test_ipc_ask_prints_ack_and_corr_then_times_out(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0

    res = run_ipc(["ask", "--to", "proj-b", "status"], cwd=tmp_path)
    # No responder is running in tests, so we expect a timeout exit code (30)
    assert res.returncode == 30, res.stdout + res.stderr
    out = (res.stdout or "").lower()
    # Should include ack and correlation (queued/ack + correlation=...)
    assert any(ack in out for ack in ["ack", "queued", "sent"])
    assert re.search(r"correlation=[\w\-]+", out) is not None
    assert "timeout" in out
