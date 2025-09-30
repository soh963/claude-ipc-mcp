"""
Contract tests for `ipc messages clear` command.
"""

from __future__ import annotations

from pathlib import Path
from tests.helpers.cli import run_ipc


def test_messages_clear_requires_init(tmp_path: Path):
    res = run_ipc(["messages", "clear", "--force"], cwd=tmp_path)
    assert res.returncode != 0
    out = (res.stderr or res.stdout or "").lower()
    assert "init" in out or "not initialized" in out


def test_messages_clear_force_succeeds(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0
    res = run_ipc(["messages", "clear", "--force"], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    out = (res.stdout or "").lower()
    assert "deleted" in out or "cleared" in out
