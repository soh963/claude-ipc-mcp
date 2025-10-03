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

# MIGRATION: Use local_broker_client (absolute rules)
import local_broker_client as broker_client
from core.logging_utils import with_logging, setup_project_logging


def check_local_broker(project_root: Path) -> dict:
    """Check local broker status and measure response time."""
    start_time = time.perf_counter()

    # Check if broker is running
    running = broker_client.is_broker_running(project_root)

    elapsed_time = time.perf_counter() - start_time
    elapsed_ms = int(elapsed_time * 1000)

    if running:
        return {
            "ok": True,
            "rtt_ms": elapsed_ms,
            "elapsed_ms": elapsed_ms,
            "mode": "local",
        }
    else:
        return {
            "ok": False,
            "rtt_ms": 0,
            "elapsed_ms": elapsed_ms,
            "mode": "local",
            "error": "Local broker not running",
        }


@with_logging("ping")
def run_ping(target: Optional[str] = None, project_root: Optional[Path] = None) -> int:
    """Run the ping command (local broker mode - absolute rules).

    Args:
        target: Ignored (local broker only)
        project_root: Project root directory (auto-detected if not provided)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Auto-detect project root (.ipc priority)
    if project_root is None:
        project_root = broker_client.detect_project_root()

    project_root = project_root.resolve()

    # Check if .ipc exists
    if not (project_root / ".ipc").exists():
        print("error: project not initialized; run 'ipc init'", file=sys.stderr)
        return 1

    # Setup logging
    setup_project_logging(project_root)

    # Check local broker status
    ping_result = check_local_broker(project_root)

    if not ping_result["ok"]:
        error_msg = ping_result.get("error", "Local broker not running")
        print(f"error: {error_msg}", file=sys.stderr)
        return 1

    # Extract metrics
    rtt_ms = ping_result["rtt_ms"]
    elapsed_ms = ping_result["elapsed_ms"]

    # Generate placeholder percentile metrics
    p95_ms = max(rtt_ms, int(rtt_ms * 1.1))
    p99_ms = max(rtt_ms, int(rtt_ms * 1.2))

    # Format output (local broker mode)
    output = (
        f"pong (local) rtt_ms={rtt_ms} p95={p95_ms}ms p99={p99_ms}ms "
        f"latency={elapsed_ms}ms broker=online mode=local"
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
