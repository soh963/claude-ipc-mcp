#!/usr/bin/env python3
"""
Launch multiple IPC AI agents concurrently.

Features:
- Ensures the singleton broker is running
- Registers N instances (unique ids)
- Optionally starts auto-responders for each instance
- Runs steps concurrently for speed

Usage:
  python tools/launch_agents.py --count 10 --prefix agent --start-responder
  python tools/launch_agents.py --count 10 --dry-run
"""
from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def ensure_broker() -> bool:
    """Ensure the broker is running using tools/start_broker.py"""
    script = REPO_ROOT / "tools" / "start_broker.py"
    result = subprocess.run([PYTHON, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + "\n" + result.stderr)
        return False
    return True


def register_instance(instance_id: str) -> Tuple[str, bool, str]:
    """Register a single instance using tools/ipc_register.py."""
    script = REPO_ROOT / "tools" / "ipc_register.py"
    result = subprocess.run(
        [PYTHON, str(script), instance_id, "--no-default"], capture_output=True, text=True
    )
    success = result.returncode == 0
    msg = result.stdout if success else (result.stderr or result.stdout)
    return instance_id, success, msg.strip()


def start_responder(instance_id: str) -> Tuple[str, bool, str]:
    """Start simple_auto_responder for an instance in background (best-effort)."""
    script = REPO_ROOT / "tools" / "simple_auto_responder.py"
    try:
        # Use os.devnull to prevent 'nul' file creation
        with open(os.devnull, 'w') as devnull:
            proc = subprocess.Popen(
                [PYTHON, str(script), instance_id], stdout=devnull, stderr=devnull
            )
        return instance_id, True, f"pid={proc.pid}"
    except Exception as exc:  # noqa: BLE001
        return instance_id, False, str(exc)


def build_instances(prefix: str, count: int) -> List[str]:
    return [f"{prefix}{i:02d}" for i in range(1, count + 1)]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Launch multiple IPC agents concurrently")
    p.add_argument("--count", type=int, default=10, help="Number of agents to create (default: 10)")
    p.add_argument(
        "--prefix", type=str, default="agent", help="Instance id prefix (default: agent)"
    )
    p.add_argument("--dry-run", action="store_true", help="Plan only; do not make changes")
    p.add_argument("--no-responder", action="store_true", help="Do not start auto-responders")
    return p.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    instances = build_instances(args.prefix, args.count)
    print(f"Planned instances ({len(instances)}): {', '.join(instances)}")

    if args.dry_run:
        print("Dry-run: skipping broker/registration/responder start.")
        return 0

    print("[1/3] Ensuring broker running...")
    if not ensure_broker():
        print("❌ Failed to ensure broker running")
        return 1
    print("✅ Broker is ready")

    print("[2/3] Registering instances in parallel...")
    reg_ok = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(instances))) as ex:
        futures = [ex.submit(register_instance, inst) for inst in instances]
        for fut in concurrent.futures.as_completed(futures):
            inst, ok, msg = fut.result()
            status = "✅" if ok else "❌"
            print(f"  {status} register {inst}: {msg}")
            reg_ok = reg_ok and ok

    if not reg_ok:
        print("⚠️  Some registrations failed. Continuing with started ones.")

    if args.no_responder:
        print("[3/3] Skipping auto-responders (--no-responder)")
        return 0

    print("[3/3] Starting auto-responders in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(instances))) as ex:
        futures = [ex.submit(start_responder, inst) for inst in instances]
        for fut in concurrent.futures.as_completed(futures):
            inst, ok, msg = fut.result()
            status = "✅" if ok else "❌"
            print(f"  {status} responder {inst}: {msg}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
