"""
Contract Test T007: IPC Init Command

Requirements:
- Creates .ipc/{config,logs,state,secret} directory structure
- Idempotent: Running multiple times is safe
- Returns non-zero exit code for incompatible major version
"""

from __future__ import annotations

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_init_creates_ipc_structure(tmp_path: Path):
    """T007.1: ipc init creates required .ipc directory structure."""
    # Run: ipc init in a temp project dir
    result = run_ipc(["init"], cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr

    # Verify .ipc and subdirs exist
    ipc = tmp_path / ".ipc"
    assert ipc.exists() and ipc.is_dir()
    for sub in ("config", "logs", "state", "secret"):
        p = ipc / sub
        assert p.exists() and p.is_dir(), f"missing {p}"

    # Verify config files created
    config_file = ipc / "config" / "settings.json"
    assert config_file.exists(), "settings.json not created"

    # Verify state file created with project_id
    state_file = ipc / "state" / "project.json"
    assert state_file.exists(), "project.json not created"

    # Check project_id format
    with open(state_file, 'r') as f:
        state = json.load(f)
        assert 'project_id' in state, "project_id not in state"
        assert state['project_id'], "project_id is empty"
        assert state['project_id'].startswith('proj_'), f"project_id format incorrect: {state['project_id']}"

    # Idempotency: run again should still succeed and keep structure
    result2 = run_ipc(["init"], cwd=tmp_path)
    assert result2.returncode == 0, result2.stdout + result2.stderr

    # Verify project_id unchanged
    with open(state_file, 'r') as f:
        state2 = json.load(f)
        assert state2['project_id'] == state['project_id'], "project_id changed on re-init"

    for sub in ("config", "logs", "state", "secret"):
        p = ipc / sub
        assert p.exists() and p.is_dir(), f"missing after rerun {p}"


def test_ipc_init_incompatible_version(tmp_path: Path):
    """T007.2: Returns non-zero exit code for incompatible major version."""
    # Create .ipc with incompatible version
    ipc = tmp_path / ".ipc"
    ipc.mkdir()
    config_dir = ipc / "config"
    config_dir.mkdir()

    # Write incompatible version
    config_file = config_dir / "settings.json"
    config_file.write_text(json.dumps({
        'version': '999.0.0',  # Future major version
        'min_compatible_version': '999.0.0'
    }))

    # Run init - should fail
    result = run_ipc(["init"], cwd=tmp_path)
    assert result.returncode != 0, "Should fail for incompatible version"

    # Check error message
    error_output = (result.stdout + result.stderr).lower()
    assert 'version' in error_output or 'incompatible' in error_output, \
        "Error should mention version incompatibility"


def test_ipc_init_preserves_secret(tmp_path: Path):
    """T007.3: Init preserves existing shared secret if present."""
    # First init
    result1 = run_ipc(["init"], cwd=tmp_path)
    assert result1.returncode == 0

    # Read initial secret if created
    secret_file = tmp_path / ".ipc" / "secret" / "shared.key"
    initial_secret = None
    if secret_file.exists():
        initial_secret = secret_file.read_text().strip()

    # Second init
    result2 = run_ipc(["init"], cwd=tmp_path)
    assert result2.returncode == 0

    # Verify secret unchanged
    if initial_secret and secret_file.exists():
        new_secret = secret_file.read_text().strip()
        assert new_secret == initial_secret, "Secret changed on re-init"


def test_ipc_init_creates_gitignore(tmp_path: Path):
    """T007.4: Init creates appropriate .gitignore in .ipc directory."""
    # Run init
    result = run_ipc(["init"], cwd=tmp_path)
    assert result.returncode == 0

    # Check .gitignore exists
    gitignore_file = tmp_path / ".ipc" / ".gitignore"
    assert gitignore_file.exists(), ".gitignore not created in .ipc"

    # Verify critical entries
    gitignore_content = gitignore_file.read_text()
    assert 'secret/' in gitignore_content or 'secret' in gitignore_content, "secret/ not in .gitignore"
    assert 'logs/' in gitignore_content or '*.log' in gitignore_content, "logs/ not in .gitignore"

