from __future__ import annotations

import pytest
from pathlib import Path
from tests.helpers.cli import run_ipc


@pytest.mark.xfail(reason="Quickstart end-to-end not implemented yet")
def test_quickstart_minimal_flow(temp_project):
    # init → status → ping
    p = Path(temp_project)
    r1 = run_ipc(["init"], cwd=p)
    assert r1.returncode == 0
    r2 = run_ipc(["status"], cwd=p)
    assert r2.returncode == 0
    r3 = run_ipc(["ping"], cwd=p)
    assert r3.returncode == 0
