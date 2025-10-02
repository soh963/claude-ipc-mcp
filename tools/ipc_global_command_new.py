#!/usr/bin/env python
"""
Updated IPC Global Command with Service Manager Integration
This is a new version that uses the service manager for broker lifecycle
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import time

# Ensure 'src' is importable for local development
SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Import broker service manager
try:
    from broker.service_manager import ServiceManager
    _service_manager_available = True
except ImportError:
    _service_manager_available = False

# Prefer core modules if available
try:
    from core.project_context import (
        ensure_layout,
        read_session,
        write_session,
        default_instance_id,
        state_file,
    )
    from core import broker_client

    _core_available = True
except Exception:
    ensure_layout = None
    read_session = None
    write_session = None
    default_instance_id = None
    state_file = None
    broker_client = None
    _core_available = False


def ensure_broker() -> None:
    """
    Ensure the TCP broker is running using Service Manager.
    This is the improved version that properly manages broker lifecycle.
    """
    if not _core_available:
        return

    # First, quick check if broker is already responding
    try:
        resp = broker_client.status()
        if resp.get("status") == "ok":
            return
    except Exception:
        pass

    # Use service manager if available
    if _service_manager_available:
        try:
            manager = ServiceManager()

            # Check if broker is running
            if manager.is_broker_running():
                return

            # Start broker using service manager
            print("Starting broker daemon via Service Manager...")
            if manager.start_broker(timeout=10):
                # Give it a moment to stabilize
                time.sleep(0.5)
                # Verify it's responding
                try:
                    resp = broker_client.status()
                    if resp.get("status") == "ok":
                        return
                except:
                    pass
        except Exception as e:
            print(f"Service Manager failed: {e}")

    # Fallback to old method if service manager not available or failed
    # This maintains backward compatibility
    try:
        import subprocess

        # Try to start broker using start_broker_new.py
        start_script = Path(__file__).parent / "start_broker_new.py"
        if start_script.exists():
            result = subprocess.run(
                [sys.executable, str(start_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Give it a moment to start
                time.sleep(0.5)
                # Verify broker is responding
                try:
                    resp = broker_client.status()
                    if resp.get("status") == "ok":
                        return
                except:
                    pass
    except Exception:
        pass

    # Last resort: Try the old importlib method
    # This is kept for absolute backward compatibility
    try:
        import importlib

        importlib.import_module("claude_ipc_server")
        # Wait until broker responds OK (up to ~1s)
        for _ in range(20):
            try:
                r = broker_client.status()
                if r.get("status") == "ok":
                    break
            except Exception:
                pass
            time.sleep(0.05)
    except Exception:
        pass


def ensure_ipc_layout(project_dir: Path) -> dict:
    """Create IPC directory structure"""
    ipc_root = project_dir / ".ipc"
    subdirs = ["config", "logs", "state", "secret"]
    created = []
    ipc_root.mkdir(exist_ok=True)
    for s in subdirs:
        p = ipc_root / s
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
    # Create minimal config/state files to satisfy contracts
    cfg_json = ipc_root / "config" / "settings.json"
    if not cfg_json.exists():
        cfg_json.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "min_compatible_version": "1.0.0",
                }
            )
        )
        created.append(str(cfg_json))
    proj_state = ipc_root / "state" / "project.json"
    if not proj_state.exists():
        # Contract expects project_id to start with 'proj_'
        proj_id = f"proj_{project_dir.name}"
        proj_state.write_text(
            json.dumps(
                {
                    "project_id": proj_id,
                }
            )
        )
        created.append(str(proj_state))
    return {"created": created}


# Add the rest of the command functions here...
# For brevity, I'm showing the key changes. The full file would include all the command functions
# from the original ipc_global_command.py but with the improved ensure_broker function

def cmd_init(args: argparse.Namespace) -> int:
    """Initialize IPC in current directory"""
    project_dir = Path.cwd()
    result = ensure_ipc_layout(project_dir)
    info = {"initialized": True, "project_dir": str(project_dir)}
    if result.get("created"):
        info["created_files"] = result["created"]

    # Initialize broker
    ensure_broker()

    # Auto-register if core is available
    if _core_available and ensure_layout and default_instance_id:
        instance = default_instance_id()
        try:
            import os as _os
            import hashlib as _hashlib
            import time as _t

            shared = _os.environ.get("IPC_SHARED_SECRET")
            auth_token = None
            if shared:
                auth_token = _hashlib.sha256(f"{instance}:{shared}".encode()).hexdigest()
            session_token = None
            for _ in range(10):  # up to ~500ms
                resp = broker_client.register(instance, auth_token=auth_token)
                if resp.get("status") == "ok" and resp.get("session_token"):
                    session_token = resp["session_token"]
                    break
                _t.sleep(0.05)
            if session_token:
                write_session(instance, session_token, Path.cwd())
                info.update({"instance_id": instance})
        except Exception:
            pass
    print(json.dumps(info))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Get broker status using Service Manager"""
    verbose = getattr(args, "verbose", False)

    # Use service manager for more detailed status
    if _service_manager_available:
        try:
            manager = ServiceManager()
            status = manager.get_broker_status()

            # Format output
            data = {
                "broker": {
                    "running": status["running"],
                    "responsive": status["responsive"],
                    "version": status.get("version", "2.0.0"),
                    "compatible": True,
                    "pid": status.get("pid")
                },
                "connections": len(status.get("instances", [])),
                "host": status["host"],
                "port": status["port"]
            }

            if verbose:
                data["instances"] = status.get("instances", [])
                data["uptime"] = status.get("uptime")
                data["total_queued"] = status.get("total_queued", 0)

                # Add health check
                healthy, message = manager.health_check()
                data["health"] = {
                    "healthy": healthy,
                    "message": message
                }

            print(json.dumps(data, indent=2 if verbose else None))
            return 0 if status["running"] else 1

        except Exception as e:
            print(json.dumps({"error": str(e)}))
            return 1

    # Fallback to old method
    try:
        from cli.commands.status_cmd import run_status

        return run_status(verbose)
    except ImportError:
        # Inline implementation as fallback
        running = False
        connections = 0

        try:
            ensure_broker()
            if broker_client:
                resp = broker_client.status()
                running = resp.get("status") == "ok"
                connections = len(resp.get("instances", []))
        except Exception:
            running = False

        data = {
            "broker": {"running": running, "version": "2.0.0", "compatible": True},
            "connections": connections,
        }

        print(json.dumps(data))
        return 0 if running else 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="IPC Global Command Tool (Improved)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    subparsers.add_parser("init", help="Initialize IPC in current directory")

    # status command
    status_parser = subparsers.add_parser("status", help="Check broker status")
    status_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # Add other commands here...
    # (For brevity, showing only key commands)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handlers
    if args.command == "init":
        return cmd_init(args)
    elif args.command == "status":
        return cmd_status(args)
    # Add other command routing here...

    return 0


if __name__ == "__main__":
    sys.exit(main())