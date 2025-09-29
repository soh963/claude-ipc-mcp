from __future__ import annotations

import json
from tests.helpers.cli import run_ipc


def test_ipc_status_reports_broker_state(temp_project):
    # Given an initialized project
    init = run_ipc(["init"], cwd=temp_project)
    assert init.returncode == 0

    # When I ask for status
    proc = run_ipc(["status"], cwd=temp_project)

    # Then: exit 0 and JSON with expected fields
    assert proc.returncode == 0
    data = json.loads(proc.stdout.strip() or "{}")
    assert "broker" in data and isinstance(data["broker"], dict)
    assert "running" in data["broker"]
