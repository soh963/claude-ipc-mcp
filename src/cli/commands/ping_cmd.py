"""IPC Ping Command Implementation

Task T025: Implements the `ipc ping` command for measuring round-trip time to broker.

Requirements:
- Send ping to broker and measure round-trip time (latency)
- Output format: `pong (local) rtt_ms=<number>` where <number> is the latency in milliseconds
- Optionally include p95/p99 metrics: `p95=<number>ms p99=<number>ms` (placeholder values acceptable)
- Must include timing information (one of: "ms", "latency", "time", "rtt", "milliseconds")
- Return exit code 0 on success
- Return exit code 1 on failure (broker offline or project not initialized)
- Check for project initialization before attempting ping
- Use retry/backoff from `src/core/retry.py` if available
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

from ._shared import ensure_broker
from core.project_context import read_session
from core import broker_client
from core.logging_utils import with_logging, setup_project_logging

# Import retry if available, fallback gracefully
try:
    from core.retry import retry

    _retry_available = True
except ImportError:
    _retry_available = False


def check_project_initialized(project_root: Optional[Path] = None) -> bool:
    """Check if the project is properly initialized with .ipc structure."""
    if project_root is None:
        project_root = Path.cwd()

    project_root = project_root.resolve()
    ipc_root = project_root / ".ipc"

    # Check if .ipc directory exists
    if not ipc_root.exists():
        return False

    # Check for critical subdirectories
    required_dirs = ["config", "state"]
    for dir_name in required_dirs:
        if not (ipc_root / dir_name).exists():
            return False

    # Check for project.json in state directory
    project_file = ipc_root / "state" / "project.json"
    if not project_file.exists():
        return False

    return True


def check_broker_reachable() -> bool:
    """Check if broker is reachable by testing status."""
    try:
        resp = broker_client.status()
        # Broker is reachable if we get any response (even error responses mean broker is up)
        return resp.get("status") in ("ok", "error")
    except Exception:
        return False


def perform_ping_with_retry(target: Optional[str] = None) -> dict:
    """Perform ping with retry logic and measure round-trip time."""
    target = target or "local"
    start_time = time.perf_counter()

    def ping_fn():
        sess = read_session()
        return broker_client.ping(session_token=sess.session_token if sess else None, target=target)

    if _retry_available:
        # Use retry logic from core.retry
        success, result = retry(ping_fn, attempts=3, timeout_s=5.0)
    else:
        # Fallback to simple retry
        success = False
        result = None
        for _ in range(3):
            try:
                result = ping_fn()
                success = True
                break
            except Exception as e:
                result = e
                time.sleep(0.2)

    elapsed_time = time.perf_counter() - start_time
    elapsed_ms = int(elapsed_time * 1000)

    if success and isinstance(result, dict):
        # Extract RTT from broker response
        rtt_ms = result.get("rtt_ms", elapsed_ms)
        ok = result.get("ok", False)

        return {"ok": ok, "rtt_ms": rtt_ms, "elapsed_ms": elapsed_ms, "target": target}
    else:
        # Ping failed, return error state
        return {
            "ok": False,
            "rtt_ms": 0,
            "elapsed_ms": elapsed_ms,
            "target": target,
            "error": str(result) if isinstance(result, Exception) else "Unknown error",
        }


@with_logging("ping")
def run_ping(target: Optional[str] = None, project_root: Optional[Path] = None) -> int:
    """Run the ping command.

    Args:
        target: Target to ping (defaults to "local")
        project_root: Project root directory (defaults to current working directory)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    if project_root is None:
        project_root = Path.cwd()

    project_root = project_root.resolve()
    target = target or "local"

    # Check if project is initialized
    if not check_project_initialized(project_root):
        print("error: project not initialized; run 'ipc init'", file=sys.stderr)
        return 1

    # Setup logging
    setup_project_logging(project_root)

    # Try to ensure broker is running
    try:
        ensure_broker()
    except Exception:
        pass  # Continue and let the ping attempt fail gracefully

    # Check if broker is reachable
    if not check_broker_reachable():
        print("error: broker offline or unreachable", file=sys.stderr)
        return 1

    # Perform ping with retry logic
    ping_result = perform_ping_with_retry(target)

    if not ping_result["ok"]:
        if "error" in ping_result:
            print(f"error: ping failed - {ping_result['error']}", file=sys.stderr)
        else:
            print("error: ping failed", file=sys.stderr)
        return 1

    # Extract metrics
    rtt_ms = ping_result["rtt_ms"]
    elapsed_ms = ping_result["elapsed_ms"]

    # Generate placeholder percentile metrics based on current measurement
    # This is acceptable per requirements: "placeholder values acceptable"
    p95_ms = max(rtt_ms, int(rtt_ms * 1.1))  # Slightly higher than RTT
    p99_ms = max(rtt_ms, int(rtt_ms * 1.2))  # Even higher for p99

    # Format output according to requirements
    # Must include: "pong (target) rtt_ms=<number>" and timing information
    # Include broker state keyword for contract expectations
    output = (
        f"pong ({target}) rtt_ms={rtt_ms} p95={p95_ms}ms p99={p99_ms}ms "
        f"latency={elapsed_ms}ms broker=online"
    )
    print(output)

    return 0


def ping_command(args=None) -> int:
    """Command entry point for CLI integration.

    Args:
        args: Command arguments with optional 'to' target

    Returns:
        Exit code
    """
    target = None
    if args and hasattr(args, "to"):
        target = args.to

    return run_ping(target)


if __name__ == "__main__":
    # Allow direct execution for testing
    sys.exit(run_ping())
