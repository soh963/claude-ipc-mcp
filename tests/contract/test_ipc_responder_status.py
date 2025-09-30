"""
Contract tests for `ipc responder status` command.
"""

from __future__ import annotations

from pathlib import Path
from tests.helpers.cli import run_ipc


def test_status_not_running_returns_62(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0
    res = run_ipc(["responder", "status", "proj-z"], cwd=tmp_path)
    assert res.returncode == 62
    assert '"running": false' in (res.stdout or '').lower()


def test_status_running_returns_0(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0
    s = run_ipc(["responder", "start", "proj-y", "--detach"], cwd=tmp_path)
    assert s.returncode == 0
    r = run_ipc(["responder", "status", "proj-y"], cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    out = (r.stdout or '').lower()
    assert '"running": true' in out
    run_ipc(["responder", "stop", "proj-y"], cwd=tmp_path)
