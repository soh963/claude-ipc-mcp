"""
Contract Test T008: IPC Status Command

Requirements:
- Shows broker version and compatibility
- Shows project_id
- Returns JSON with broker status, connections, last_ping_ms
"""

from __future__ import annotations

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_status_minimal_schema(tmp_path: Path):
    """T008.1: ipc status returns JSON with required schema."""
    # Initialize project first
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0, "Init failed"

    res = run_ipc(["status"], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr

    # Output should be JSON with expected top-level keys
    data = json.loads(res.stdout.strip() or "{}")
    assert isinstance(data, dict)
    assert "broker" in data and isinstance(data["broker"], dict)
    # broker.running key must exist (bool expected, may be False)
    assert "running" in data["broker"]
    # connections integer presence
    assert "connections" in data
    # last_ping_ms key present (value may be None)
    assert "last_ping_ms" in data


def test_ipc_status_shows_project_id(tmp_path: Path):
    """T008.2: ipc status includes project_id in output."""
    # Initialize project
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0

    # Get project_id from state file
    state_file = tmp_path / ".ipc" / "state" / "project.json"
    with open(state_file, 'r') as f:
        state = json.load(f)
        expected_project_id = state['project_id']

    # Run status
    result = run_ipc(["status"], cwd=tmp_path)
    assert result.returncode == 0

    # Parse JSON output
    data = json.loads(result.stdout.strip() or "{}")

    # Check project_id exists
    assert "project_id" in data or "projectId" in data, \
        "project_id not in status output"

    # Verify it matches
    actual_project_id = data.get("project_id") or data.get("projectId")
    assert actual_project_id == expected_project_id, \
        f"project_id mismatch: {actual_project_id} != {expected_project_id}"


def test_ipc_status_broker_version(tmp_path: Path):
    """T008.3: ipc status shows broker version and compatibility."""
    # Initialize project
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0

    # Run status
    result = run_ipc(["status"], cwd=tmp_path)
    assert result.returncode == 0

    # Parse output
    data = json.loads(result.stdout.strip() or "{}")

    # Check broker info exists
    assert "broker" in data, "broker field missing"
    broker = data["broker"]

    # Should have version info
    assert "version" in broker or "compatible" in broker or "compat" in broker, \
        "Broker should include version or compatibility info"


def test_ipc_status_without_init(tmp_path: Path):
    """T008.4: ipc status handles uninitialized project gracefully."""
    # Run status without init
    result = run_ipc(["status"], cwd=tmp_path)

    # Should either fail with clear message or show uninitialized state
    if result.returncode != 0:
        error_output = (result.stdout + result.stderr).lower()
        assert any(word in error_output for word in ['not initialized', 'init', 'initialize']), \
            "Error should mention initialization needed"
    else:
        # If it succeeds, parse JSON and check for indication
        try:
            data = json.loads(result.stdout.strip() or "{}")
            # Should indicate project not initialized somehow
            assert "project_id" not in data or data.get("initialized") is False, \
                "Should indicate project not initialized"
        except json.JSONDecodeError:
            # Non-JSON output is acceptable for error case
            pass


def test_ipc_status_connection_info(tmp_path: Path):
    """T008.5: ipc status includes connection count and ping metrics."""
    # Initialize project
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0

    # Run status
    result = run_ipc(["status"], cwd=tmp_path)
    assert result.returncode == 0

    # Parse output
    data = json.loads(result.stdout.strip() or "{}")

    # Check connections field
    assert "connections" in data, "connections field missing"
    assert isinstance(data["connections"], int), "connections should be an integer"
    assert data["connections"] >= 0, "connections should be non-negative"

    # Check last_ping_ms field
    assert "last_ping_ms" in data, "last_ping_ms field missing"
    # Value can be None or a number
    if data["last_ping_ms"] is not None:
        assert isinstance(data["last_ping_ms"], (int, float)), \
            "last_ping_ms should be a number when not None"
        assert data["last_ping_ms"] >= 0, "last_ping_ms should be non-negative"


def test_ipc_status_broker_running_state(tmp_path: Path):
    """T008.6: ipc status correctly reports broker running state."""
    # Initialize project
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0

    # Run status
    result = run_ipc(["status"], cwd=tmp_path)
    assert result.returncode == 0

    # Parse output
    data = json.loads(result.stdout.strip() or "{}")

    # Check broker running state
    assert "broker" in data, "broker field missing"
    assert "running" in data["broker"], "broker.running field missing"
    assert isinstance(data["broker"]["running"], bool), \
        "broker.running should be a boolean"

