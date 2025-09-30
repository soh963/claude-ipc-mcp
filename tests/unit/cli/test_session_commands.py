from __future__ import annotations

from pathlib import Path
from tests.helpers.cli import run_ipc

def test_session_show_and_clear(temp_project):
    p = Path(temp_project)
    # Initially no session
    r0 = run_ipc(["session", "--show"], cwd=p)
    assert r0.returncode == 0
    assert "no session" in r0.stdout

    # init may auto-register and create a session (best-effort). Regardless, session --clear should be idempotent.
    r1 = run_ipc(["init"], cwd=p)
    assert r1.returncode == 0

    # show should either display json or print no session; we accept both, but then clear and re-check.
    r2 = run_ipc(["session", "--show"], cwd=p)
    assert r2.returncode == 0

    # clear should succeed even if absent
    r3 = run_ipc(["session", "--clear"], cwd=p)
    assert r3.returncode == 0
    assert "session cleared" in r3.stdout or "no session" in r3.stdout

    # show should now be no session
    r4 = run_ipc(["session", "--show"], cwd=p)
    assert r4.returncode == 0
    assert "no session" in r4.stdout
