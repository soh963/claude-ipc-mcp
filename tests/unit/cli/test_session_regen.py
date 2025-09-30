from __future__ import annotations

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_session_regen_creates_and_is_idempotent(temp_project):
    p = Path(temp_project)

    # Ensure no session initially
    r0 = run_ipc(["session", "--show"], cwd=p)
    assert r0.returncode == 0
    assert r0.stdout.strip() == "no session"

    # Regen should create a session and print JSON
    r1 = run_ipc(["session", "--regen"], cwd=p)
    assert r1.returncode == 0
    data1 = json.loads(r1.stdout.strip())
    assert "instance_id" in data1 and "session_token" in data1

    # Show should now return JSON with same instance_id
    r2 = run_ipc(["session", "--show"], cwd=p)
    assert r2.returncode == 0
    data2 = json.loads(r2.stdout.strip())
    assert data1["instance_id"] == data2["instance_id"]

    # Regen again should succeed and return a (possibly different) session token
    r3 = run_ipc(["session", "--regen"], cwd=p)
    assert r3.returncode == 0
    data3 = json.loads(r3.stdout.strip())
    assert data3["instance_id"] == data2["instance_id"]
    assert data3["session_token"]
