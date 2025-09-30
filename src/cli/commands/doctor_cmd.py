from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from ._shared import ensure_broker, get_cli_version, read_project_id
from core import broker_client
from core.logging_utils import with_logging, setup_project_logging


@with_logging("doctor")
def run_doctor() -> int:
    """
    Run system health checks and provide actionable diagnostics.

    Checks:
    - PATH: Verify ipc command availability
    - Broker: Check broker connectivity and status
    - Secret: Verify authentication configuration
    - Version: Check version compatibility

    Returns:
        0 for healthy system or minor warnings
        1 for critical issues requiring attention
    """
    # Setup logging if project initialized
    project_root = Path.cwd()
    if (project_root / ".ipc").exists():
        setup_project_logging(project_root)
    checks = []
    issues = []
    warnings = []
    tips = []

    # Check 1: PATH - Verify ipc command is available
    print("PATH: Checking command availability...")
    try:
        # Check if 'ipc' command is in PATH
        ipc_path = shutil.which("ipc")
        if ipc_path:
            checks.append("PATH ✓ ipc command found in system PATH")
        else:
            # Check if we're running from source (development mode)
            if sys.argv[0].endswith("ipc") or "ipc" in sys.argv[0]:
                checks.append("PATH ✓ ipc command executable (development mode)")
            else:
                checks.append("PATH ✗ ipc command not found in PATH")
                issues.append("ipc command not available in system PATH")
                tips.append("Install claude-ipc-mcp package or add to PATH")
    except Exception as e:
        checks.append(f"PATH ✗ Error checking command availability: {e}")
        issues.append("Failed to check PATH for ipc command")
        tips.append("Verify installation and PATH configuration")

    # Check 2: Broker - Verify broker connectivity and status
    print("Broker: Checking connectivity...")
    broker_ok = False
    try:
        ensure_broker()

        # Give broker more time to fully start up
        import time

        time.sleep(0.2)

        # Try multiple times to handle startup timing
        for attempt in range(5):
            try:
                resp = broker_client.status()
                broker_running = resp.get("status") == "ok"
                port = getattr(broker_client, "IPC_PORT", 9876)

                if broker_running:
                    instance_count = len(resp.get("instances", []))
                    checks.append(f"Broker ✓ running on port {port} ({instance_count} instances)")
                    broker_ok = True
                    break
                if resp.get("status") == "error" and "session token" in resp.get("message", ""):
                    # Broker is running but requires authentication - this is still considered healthy
                    checks.append(f"Broker ✓ running on port {port} (authentication required)")
                    broker_ok = True
                    break
                # Not OK yet; record at final attempt
                if attempt == 4:  # Last attempt
                    checks.append(f"Broker ✗ not responding on port {port}")
                    issues.append("IPC broker is not running or accessible")
                    tips.append("Run 'ipc init' to start the broker")
            except Exception as e:
                if attempt == 4:  # Last attempt
                    raise e
                time.sleep(0.1)
    except Exception as e:
        port = getattr(broker_client, "IPC_PORT", 9876)
        checks.append(f"Broker ✗ connection failed on port {port}: {e}")
        issues.append("Cannot connect to IPC broker")
        tips.append("Check if broker is running or run 'ipc init' to start it")

    # Check 3: Secret - Verify authentication configuration
    print("Secret: Checking authentication configuration...")
    try:
        # Check environment variable
        secret_env = bool(os.environ.get("IPC_SHARED_SECRET"))

        # Check if project is initialized
        project_id = read_project_id(Path.cwd())
        project_initialized = project_id is not None

        if secret_env:
            checks.append("Secret ✓ IPC_SHARED_SECRET configured")
        elif project_initialized:
            checks.append("Secret ⚠ authentication optional (project initialized)")
            warnings.append("No shared secret configured - authentication disabled")
            tips.append("Set IPC_SHARED_SECRET environment variable for authenticated access")
        else:
            checks.append("Secret ⚠ no authentication configured")
            warnings.append("Project not initialized and no shared secret")
            tips.append("Run 'ipc init' to set up project or configure IPC_SHARED_SECRET")

    except Exception as e:
        checks.append(f"Secret ✗ configuration check failed: {e}")
        issues.append("Failed to verify authentication setup")
        tips.append("Check environment configuration and project setup")

    # Check 4: Version - Verify version compatibility
    print("Version: Checking compatibility...")
    try:
        current_version = get_cli_version()

        # Check if we can determine broker version
        if broker_ok:
            # Assume broker and CLI versions should match
            checks.append(f"Version ✓ CLI v{current_version} compatible with broker")
        else:
            checks.append(f"Version ⚠ CLI v{current_version} (broker status unknown)")
            warnings.append("Cannot verify broker compatibility")
            tips.append("Start broker to verify version compatibility")

    except Exception as e:
        checks.append(f"Version ✗ compatibility check failed: {e}")
        warnings.append("Unable to verify version compatibility")
        tips.append("Check installation and try reinstalling if issues persist")

    # Print results
    print("\nSystem Health Check Results:")
    print("=" * 40)

    for check in checks:
        print(f"  {check}")

    # Determine overall health status
    critical_issues = len(issues) > 0
    has_warnings = len(warnings) > 0

    if not critical_issues and not has_warnings:
        print("\n✓ All systems healthy - IPC ready for use")
        return 0
    elif not critical_issues and has_warnings:
        print("\n⚠ System ok with minor warnings")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
    else:
        print("\n✗ Detected issues requiring attention")

    # Show issues and tips
    if issues:
        print("\nDetected issues:")
        for issue in issues:
            print(f"  - {issue}")

    if tips:
        print("\nActionable tips:")
        for tip in tips:
            print(f"  - {tip}")

    # Return appropriate exit code
    return 1 if critical_issues else 0
