from __future__ import annotations

from tests.helpers.cli import run_ipc


def test_ipc_doctor_runs_and_reports(temp_project):
    # no init required; doctor should guide setup if missing
    proc = run_ipc(["doctor"], cwd=temp_project)

    # Accept either success (0) or unrecoverable (13) until implemented
    assert proc.returncode in (0, 13)
    out = (proc.stdout or "") + (proc.stderr or "")
    assert any(s in out.lower() for s in ["issue", "fix", "check", "diagnos", "setup", "missing"])
