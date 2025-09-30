from __future__ import annotations

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_status_verbose_contains_auth_and_session(temp_project):
    p = Path(temp_project)
    # ensure init creates layout
    r0 = run_ipc(["init"], cwd=p)
    assert r0.returncode == 0
    r1 = run_ipc(["status", "--verbose"], cwd=p)
    assert r1.returncode == 0
    data = json.loads(r1.stdout.strip())
    assert "broker" in data and isinstance(data["broker"], dict)
    # auth key exists when verbose
    assert "auth" in data and isinstance(data["auth"], dict)
    assert "shared_secret_configured" in data["auth"]
    # session key exists; value may be None before registration
    assert "session" in data
