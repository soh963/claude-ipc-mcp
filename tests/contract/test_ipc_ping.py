from __future__ import annotations

from tests.helpers.cli import run_ipc


def test_ipc_ping_returns_pong(temp_project):
    init = run_ipc(["init"], cwd=temp_project)
    assert init.returncode == 0

    proc = run_ipc(["ping"], cwd=temp_project)
    assert proc.returncode == 0
    out = (proc.stdout or "").lower()
    assert "pong" in out
