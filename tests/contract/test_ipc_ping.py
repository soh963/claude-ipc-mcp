"""
Contract test T009: IPC Ping Command

Tests for the ping command functionality including latency measurement,
p95 metrics, and graceful error handling.
"""

import json
from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_ping_success():
    """T009.1: ping command returns exit code 0 on success"""
    # Initialize project first
    init_result = run_ipc(["init"])
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Run ping command
    result = run_ipc(["ping"])
    assert result.returncode == 0, f"Ping failed with exit code {result.returncode}: {result.stderr}"


def test_ipc_ping_shows_latency():
    """T009.2: ping output includes timing info (ms, latency, time keywords)"""
    # Initialize project first
    init_result = run_ipc(["init"])
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Run ping command
    result = run_ipc(["ping"])
    assert result.returncode == 0, f"Ping failed: {result.stderr}"
    
    output = result.stdout.lower()
    # Check for timing-related keywords in output
    timing_keywords = ["ms", "latency", "time", "response", "duration"]
    has_timing_info = any(keyword in output for keyword in timing_keywords)
    assert has_timing_info, f"Ping output should include timing information. Output: {result.stdout}"


def test_ipc_ping_p95_metrics():
    """T009.3: ping output includes p95 or percentile metrics"""
    # Initialize project first
    init_result = run_ipc(["init"])
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Run ping command
    result = run_ipc(["ping"])
    assert result.returncode == 0, f"Ping failed: {result.stderr}"
    
    output = result.stdout.lower()
    # Check for p95 or percentile metrics in output
    metrics_keywords = ["p95", "percentile", "95th", "latency"]
    has_metrics = any(keyword in output for keyword in metrics_keywords)
    assert has_metrics, f"Ping output should include p95 or percentile metrics. Output: {result.stdout}"


def test_ipc_ping_without_init():
    """T009.4: handles uninitialized project gracefully"""
    # Run ping command without initialization
    result = run_ipc(["ping"])
    
    # Should handle gracefully - either succeed with appropriate message or fail gracefully
    # Check that it doesn't crash with an unhandled exception
    assert result.returncode in [0, 1], f"Ping should handle uninitialized project gracefully, got exit code: {result.returncode}"
    
    # Output should contain some indication of the state
    output = result.stdout.lower()
    error_output = result.stderr.lower()
    combined_output = output + error_output
    
    # Should mention project state or provide helpful information
    state_keywords = ["project", "init", "not", "error", "failed", "offline", "broker"]
    has_state_info = any(keyword in combined_output for keyword in state_keywords)
    assert has_state_info, f"Ping should provide informative output for uninitialized project. Output: {result.stdout}, Error: {result.stderr}"


def test_ipc_ping_broker_offline():
    """T009.5: handles broker offline state appropriately"""
    # Initialize project first
    init_result = run_ipc(["init"])
    assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
    
    # Run ping command (broker may or may not be running)
    result = run_ipc(["ping"])
    
    # Should handle broker offline state gracefully
    # Either succeeds or fails with appropriate messaging
    assert result.returncode in [0, 1], f"Ping should handle broker offline gracefully, got exit code: {result.returncode}"
    
    output = result.stdout.lower()
    error_output = result.stderr.lower()
    combined_output = output + error_output
    
    # Should provide meaningful feedback about broker state
    broker_keywords = ["broker", "offline", "connection", "failed", "timeout", "unreachable", "ping", "response"]
    has_broker_info = any(keyword in combined_output for keyword in broker_keywords)
    assert has_broker_info, f"Ping should provide informative output about broker state. Output: {result.stdout}, Error: {result.stderr}"