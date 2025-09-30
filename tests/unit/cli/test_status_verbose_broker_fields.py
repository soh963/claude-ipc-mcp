from __future__ import annotations

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_status_verbose_includes_broker_port_and_version_tolerant(temp_project):
    p = Path(temp_project)
    r0 = run_ipc(["init"], cwd=p)
    assert r0.returncode == 0

    r1 = run_ipc(["status", "--verbose"], cwd=p)
    assert r1.returncode == 0
    data = json.loads(r1.stdout.strip())

    assert "broker" in data and isinstance(data["broker"], dict)
    # Port should be present and either None or an int (static default 9876)
    assert "port" in data["broker"]
    port = data["broker"]["port"]
    assert (port is None) or isinstance(port, int)

    # Version may be None when running from source; accept either None or non-empty string
    assert "version" in data["broker"]
    version = data["broker"]["version"]
    assert (version is None) or (isinstance(version, str) and len(version) > 0)
