"""
Contract test T010: IPC Chat Command

Test the chat command functionality including message sending,
acknowledgment display, and correlation ID handling.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_chat_sends_message(tmp_path: Path):
    """T010.1: chat --to target 'Hello' returns exit code 0 and shows ack"""
    # Initialize project first
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Send chat message
    result = run_ipc(["chat", "--to", "test_target", "Hello"], cwd=tmp_path)
    assert result.returncode == 0, f"Chat failed: {result.stdout}\n{result.stderr}"
    
    # Check for acknowledgment in output
    output = (result.stdout or "").lower()
    assert any(ack in output for ack in ["ack", "acknowledgment", "sent"]), (
        f"No acknowledgment found in output: {result.stdout}"
    )


def test_ipc_chat_shows_correlation_id(tmp_path: Path):
    """T010.2: chat response includes corr_id or correlation_id"""
    # Initialize project first
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Send chat message
    result = run_ipc(["chat", "--to", "test_target", "Hello world"], cwd=tmp_path)
    assert result.returncode == 0, f"Chat failed: {result.stdout}\n{result.stderr}"
    
    output = result.stdout or ""
    
    # Check for correlation ID patterns
    correlation_patterns = [
        r"correlation[_\-]?id[:=]\s*[\w\-]+",  # correlation_id: or correlation-id=
        r"corr[_\-]?id[:=]\s*[\w\-]+",        # corr_id: or corr-id=
        r"correlation[:=]\s*[\w\-]+",          # correlation:
        r"corr[:=]\s*[\w\-]+",                 # corr:
    ]
    
    found_correlation = False
    for pattern in correlation_patterns:
        if re.search(pattern, output.lower()):
            found_correlation = True
            break
    
    assert found_correlation, (
        f"No correlation ID found in output: {output}"
    )


def test_ipc_chat_missing_to_parameter(tmp_path: Path):
    """T010.3: handles missing --to parameter gracefully with error"""
    # Initialize project first
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Try to send chat without --to parameter
    result = run_ipc(["chat", "Hello without target"], cwd=tmp_path)
    
    # Should fail gracefully
    assert result.returncode != 0, "Chat without --to should fail"
    
    # Check error message mentions missing recipient/target
    error_output = (result.stderr or result.stdout or "").lower()
    assert any(keyword in error_output for keyword in [
        "missing", "required", "recipient", "target", "--to", "usage"
    ]), f"Error message should mention missing --to parameter: {error_output}"


def test_ipc_chat_empty_message(tmp_path: Path):
    """T010.4: handles empty message appropriately"""
    # Initialize project first
    init_result = run_ipc(["init"], cwd=tmp_path)
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Try to send empty message
    result = run_ipc(["chat", "--to", "test_target", ""], cwd=tmp_path)
    
    # Should handle gracefully (either accept or reject with clear message)
    if result.returncode != 0:
        # If rejected, should have clear error message
        error_output = (result.stderr or result.stdout or "").lower()
        assert any(keyword in error_output for keyword in [
            "empty", "message", "content", "required"
        ]), f"Error for empty message should be clear: {error_output}"
    else:
        # If accepted, should still show acknowledgment
        output = (result.stdout or "").lower()
        assert any(ack in output for ack in ["ack", "acknowledgment", "sent"]), (
            f"Empty message should still show acknowledgment: {result.stdout}"
        )


def test_ipc_chat_without_init(tmp_path: Path):
    """T010.5: handles uninitialized project gracefully"""
    # Do NOT initialize project - test uninitialized state
    
    # Try to send chat message without initialization
    result = run_ipc(["chat", "--to", "test_target", "Hello"], cwd=tmp_path)
    
    # Should fail gracefully
    assert result.returncode != 0, "Chat in uninitialized project should fail"
    
    # Check error message mentions initialization or configuration
    error_output = (result.stderr or result.stdout or "").lower()
    assert any(keyword in error_output for keyword in [
        "not initialized", "init", "setup", "configure", "project"
    ]), f"Error should mention initialization: {error_output}"


def test_ipc_chat_echoes_target_and_corr(tmp_path: Path):
    """T010.6: Original test - echoes target and correlation ID"""
    # Ensure project is initialized so read_session doesn't break
    (tmp_path / ".ipc").mkdir(exist_ok=True)

    msg = "Hello contract test"
    res = run_ipc(["chat", "--to", "self", msg], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr

    out = (res.stdout or "").strip().lower()
    assert "to=self" in out
    assert "correlation=" in out
    # corr format corr-<digits>
    assert re.search(r"correlation=corr-\d+", out) is not None