"""
Contract tests for `ipc responder` command.
Focus on start/stop idempotent behavior, PID file handling, and exit codes.
"""

from __future__ import annotations

import os
from pathlib import Path
from tests.helpers.cli import run_ipc


def _pid_path(instance: str) -> Path:
    data_dir = Path(os.path.expandvars(r"%USERPROFILE%\.claude-ipc-data"))
    return data_dir / "responders" / f"{instance}.pid"


def test_responder_start_creates_pid_and_is_idempotent(tmp_path: Path):
    # init project to satisfy CLI preconditions
    init = run_ipc(["init"], cwd=tmp_path)
    assert init.returncode == 0

    inst = "proj-x"
    pid_file = _pid_path(inst)
    if pid_file.exists():
        try:
            pid_file.unlink()
        except Exception:
            pass

    # start
    res1 = run_ipc(["responder", "start", inst, "--detach"], cwd=tmp_path)
    assert res1.returncode == 0, res1.stdout + res1.stderr
    assert pid_file.exists(), f"PID file not created: {pid_file}"

    # start again (idempotent)
    res2 = run_ipc(["responder", "start", inst, "--detach"], cwd=tmp_path)
    assert res2.returncode == 0, res2.stdout + res2.stderr
    assert pid_file.exists(), "PID file should still exist"

    # stop
    res3 = run_ipc(["responder", "stop", inst], cwd=tmp_path)
    assert res3.returncode == 0, res3.stdout + res3.stderr
    # stop again (idempotent)
    res4 = run_ipc(["responder", "stop", inst], cwd=tmp_path)
    assert res4.returncode == 0, res4.stdout + res4.stderr
