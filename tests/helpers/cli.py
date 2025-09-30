from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _ipc_script_path() -> Path:
    """Resolve absolute path to tools/ipc_global_command.py from this file."""
    return Path(__file__).resolve().parents[2] / "tools" / "ipc_global_command.py"


def run_ipc(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run the IPC CLI via tools/ipc_global_command.py.

    - args: list of CLI args, e.g., ["init"] or ["ping", "--to", "local"]
    - cwd: optional working directory path

    Returns subprocess.CompletedProcess with stdout/stderr captured.
    """
    script = _ipc_script_path()
    cmd = [sys.executable, str(script), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )


def setup_test_project(path: Path, with_broker: bool = False) -> Dict[str, Any]:
    """Set up a test project with IPC initialization.

    Args:
        path: Directory to initialize as IPC project
        with_broker: Whether to start a broker instance (for integration tests)

    Returns:
        Dict with project_id, state_file, config_file paths
    """
    # Run init
    result = run_ipc(["init"], cwd=path)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to initialize project: {result.stderr}")

    # Read project state
    state_file = path / ".ipc" / "state" / "project.json"
    config_file = path / ".ipc" / "config" / "settings.json"

    project_info = {
        "project_path": path,
        "state_file": state_file,
        "config_file": config_file,
        "project_id": None
    }

    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
            project_info["project_id"] = state.get("project_id")

    return project_info


def parse_json_output(output: str) -> Union[Dict[str, Any], None]:
    """Parse JSON from command output, handling extra text.

    Args:
        output: Raw stdout from command

    Returns:
        Parsed JSON dict or None if not valid JSON
    """
    # Try to parse as-is first
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from output (might have logging)
    lines = output.strip().split('\n')
    for line in reversed(lines):  # Check from end (most likely location)
        if line.strip().startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    return None


def wait_for_broker(timeout: float = 5.0) -> bool:
    """Wait for broker to be available.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        True if broker is available, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = run_ipc(["ping"])
        if result.returncode == 0:
            return True
        time.sleep(0.5)
    return False


def extract_correlation_id(output: str) -> Optional[str]:
    """Extract correlation ID from chat output.

    Args:
        output: Raw output from chat command

    Returns:
        Correlation ID if found, None otherwise
    """
    import re

    # Try multiple patterns
    patterns = [
        r'corr[-_](\d+)',
        r'correlation[-_:]?\s*(\w+)',
        r'correlation_id[-_:]?\s*(\w+)',
        r'corr_id[-_:]?\s*(\w+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1) if match.lastindex else match.group(0)

    return None


def assert_acknowledgment(output: str) -> None:
    """Assert that output contains acknowledgment indicators.

    Args:
        output: Command output to check

    Raises:
        AssertionError if no acknowledgment found
    """
    ack_indicators = ["ack", "acknowledgment", "acknowledged", "sent", "delivered", "queued"]
    output_lower = output.lower()

    assert any(indicator in output_lower for indicator in ack_indicators), \
        f"No acknowledgment found in output: {output}"


def assert_timing_info(output: str) -> None:
    """Assert that output contains timing/latency information.

    Args:
        output: Command output to check

    Raises:
        AssertionError if no timing info found
    """
    timing_indicators = ["ms", "latency", "time", "rtt", "ping", "pong", "milliseconds"]
    output_lower = output.lower()

    assert any(indicator in output_lower for indicator in timing_indicators), \
        f"No timing information found in output: {output}"
