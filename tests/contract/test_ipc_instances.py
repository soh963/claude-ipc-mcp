"""
Contract tests for `ipc instances` commands: reset and delete.
"""

from __future__ import annotations

from pathlib import Path
from tests.helpers.cli import run_ipc


def test_instances_reset_requires_init(tmp_path: Path):
    res = run_ipc(["instances", "reset"], cwd=tmp_path)
    assert res.returncode != 0
    out = (res.stderr or res.stdout or "").lower()
    assert "init" in out or "not initialized" in out


def test_instances_reset_after_init(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0
    res = run_ipc(["instances", "reset"], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr


def test_instances_delete_nonexistent(tmp_path: Path):
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0
    res = run_ipc(["instances", "delete", "nope"], cwd=tmp_path)
    assert res.returncode in (0, 51)  # ok if treated as idempotent, else 51 per spec
