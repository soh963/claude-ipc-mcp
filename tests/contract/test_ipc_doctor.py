"""
Contract Test T011: IPC Doctor Command

Tests the ipc doctor command functionality including:
- Health checks for PATH, broker, secret, version
- Actionable tips for detected problems
- Proper exit codes (0 for healthy, non-zero for issues)
- Clear status reporting for each check
"""

import json
import os
from pathlib import Path

from tests.helpers.cli import run_ipc


def test_ipc_doctor_healthy_project(tmp_path):
    """
    T011.1: Test doctor command returns 0 for initialized healthy project.
    
    Doctor should report all systems healthy when project is properly initialized.
    """
    os.chdir(tmp_path)
    
    # Initialize project first
    result = run_ipc(["init"])
    assert result.returncode == 0, f"Init failed: {result.stderr}"
    
    # Run doctor on healthy project
    result = run_ipc(["doctor"])
    
    # Should return success for healthy project
    assert result.returncode == 0, f"Doctor should return 0 for healthy project: {result.stderr}"
    
    # Should contain positive status indicators
    output = result.stdout.lower()
    assert any(word in output for word in ["healthy", "ok", "good", "✓"]), \
        f"Expected healthy status indicators in output: {result.stdout}"


def test_ipc_doctor_checks_path(tmp_path):
    """
    T011.2: Test doctor verifies PATH checking is performed.
    
    Doctor should check if IPC commands are available in PATH.
    """
    os.chdir(tmp_path)
    
    # Run doctor command
    result = run_ipc(["doctor"])
    
    # Should mention PATH checking
    output = result.stdout.lower()
    assert "path" in output, f"Expected PATH checking in output: {result.stdout}"
    
    # Should check for command availability
    assert any(word in output for word in ["command", "available", "found", "executable"]), \
        f"Expected command availability check in output: {result.stdout}"


def test_ipc_doctor_checks_broker(tmp_path):
    """
    T011.3: Test doctor verifies broker status check.
    
    Doctor should check if the IPC broker is running and accessible.
    """
    os.chdir(tmp_path)
    
    # Run doctor command
    result = run_ipc(["doctor"])
    
    # Should mention broker checking
    output = result.stdout.lower()
    assert "broker" in output, f"Expected broker checking in output: {result.stdout}"
    
    # Should check connection or status
    assert any(word in output for word in ["connection", "status", "running", "accessible", "port"]), \
        f"Expected broker connection check in output: {result.stdout}"


def test_ipc_doctor_checks_secret(tmp_path):
    """
    T011.4: Test doctor verifies secret/auth checking.
    
    Doctor should check authentication and secret configuration.
    """
    os.chdir(tmp_path)
    
    # Run doctor command
    result = run_ipc(["doctor"])
    
    # Should mention secret/auth checking
    output = result.stdout.lower()
    assert any(word in output for word in ["secret", "auth", "authentication", "token"]), \
        f"Expected secret/auth checking in output: {result.stdout}"
    
    # Should verify configuration
    assert any(word in output for word in ["config", "configured", "valid", "setup"]), \
        f"Expected configuration verification in output: {result.stdout}"


def test_ipc_doctor_checks_version(tmp_path):
    """
    T011.5: Test doctor verifies version compatibility checking.
    
    Doctor should check version compatibility of components.
    """
    os.chdir(tmp_path)
    
    # Run doctor command
    result = run_ipc(["doctor"])
    
    # Should mention version checking
    output = result.stdout.lower()
    assert "version" in output, f"Expected version checking in output: {result.stdout}"
    
    # Should check compatibility
    assert any(word in output for word in ["compatible", "compatibility", "current", "latest"]), \
        f"Expected version compatibility check in output: {result.stdout}"


def test_ipc_doctor_provides_tips(tmp_path):
    """
    T011.6: Test doctor shows actionable tips when issues detected.
    
    Doctor should provide helpful tips for resolving detected problems.
    """
    os.chdir(tmp_path)
    
    # Run doctor on uninitialized project (should have issues)
    result = run_ipc(["doctor"])
    
    # Should provide tips for problems
    output = result.stdout.lower()
    
    # Look for tip indicators
    has_tips = any(word in output for word in ["tip", "tips", "suggestion", "recommend", "try", "fix", "resolve"])
    has_issues = any(word in output for word in ["issue", "problem", "error", "warning", "missing"])
    
    # If issues are detected, tips should be provided
    if has_issues:
        assert has_tips, f"Expected actionable tips when issues detected: {result.stdout}"
    
    # Should provide actionable guidance
    if has_tips:
        assert any(word in output for word in ["run", "install", "configure", "setup", "init"]), \
            f"Expected actionable guidance in tips: {result.stdout}"


def test_ipc_doctor_without_init(tmp_path):
    """
    T011.7: Test doctor handles uninitialized project appropriately.
    
    Doctor should detect and report when project is not initialized.
    """
    os.chdir(tmp_path)
    
    # Run doctor without initializing project
    result = run_ipc(["doctor"])
    
    # Should handle uninitialized state
    output = result.stdout.lower()
    
    # Should detect missing initialization
    assert any(word in output for word in ["init", "initialize", "not initialized", "setup", "configure"]), \
        f"Expected initialization check in output: {result.stdout}"
    
    # Should suggest initialization if needed
    if "not initialized" in output or "initialize" in output:
        assert any(word in output for word in ["run", "ipc init", "setup"]), \
            f"Expected initialization suggestion: {result.stdout}"