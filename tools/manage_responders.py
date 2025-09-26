#!/usr/bin/env python3
"""Utility to inspect and stop running IPC auto-responder processes."""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

# Try to use psutil when available for cross-platform process inspection
try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore

RESPONDER_KEYWORDS = (
    "simple_auto_responder.py",
    "STABLE_AUTO_RESPONDER.py",
    "robust_auto_responder.py",
    "smart_auto_responder.py",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


@dataclass
class ResponderProcess:
    pid: int
    executable: str
    cmdline: Sequence[str]

    def matches_instance(self, instance: str | None) -> bool:
        if not instance:
            return True
        lower = " ".join(self.cmdline).lower()
        return instance.lower() in lower

    def stop(self) -> None:
        if psutil:  # pragma: no branch - prefer psutil when available
            try:
                proc = psutil.Process(self.pid)
                proc.terminate()
                proc.wait(timeout=3)
                return
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        else:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/PID", str(self.pid)], check=False)
            else:
                try:
                    os.kill(self.pid, signal.SIGTERM)
                except Exception:
                    pass


def find_responders() -> List[ResponderProcess]:
    responders: List[ResponderProcess] = []

    if psutil:  # pragma: no branch
        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any(keyword in " ".join(cmdline) for keyword in RESPONDER_KEYWORDS):
                    responders.append(
                        ResponderProcess(
                            pid=proc.info["pid"],
                            executable=proc.info.get("name", ""),
                            cmdline=tuple(cmdline),
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):  # pragma: no cover
                continue
    else:  # pragma: no cover - fallback when psutil missing
        if os.name == "nt":
            result = subprocess.run(
                ["wmic", "process", "get", "ProcessId,CommandLine"],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in result.stdout.splitlines():
                if any(keyword in line for keyword in RESPONDER_KEYWORDS):
                    try:
                        cmd, pid = line.rsplit(None, 1)
                        responders.append(ResponderProcess(int(pid), "python", cmd.split()))
                    except ValueError:
                        continue
        else:
            result = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                if any(keyword in line for keyword in RESPONDER_KEYWORDS):
                    try:
                        pid, cmd = line.strip().split(" ", 1)
                        responders.append(ResponderProcess(int(pid), "python", cmd.split()))
                    except ValueError:
                        continue

    return responders


def format_responder(proc: ResponderProcess) -> str:
    cmdline = " ".join(proc.cmdline)
    return f"PID {proc.pid:>6} | {proc.executable:<15} | {cmdline}"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List or terminate running IPC auto-responders.")
    parser.add_argument("--instance", help="Filter by instance id (case-insensitive).", default=None)
    parser.add_argument("--stop", action="store_true", help="Terminate matching responders.")
    parser.add_argument("--stop-all", action="store_true", help="Terminate every detected responder.")
    parser.add_argument("--dry-run", action="store_true", help="Show matches without taking action.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> None:
    args = parse_args(argv)
    responders = find_responders()

    if not responders:
        print("No auto-responder processes found.")
        return

    filtered = [proc for proc in responders if proc.matches_instance(args.instance)]

    if not filtered:
        print("No matching responders for the given criteria.")
        return

    action = "Listing" if not (args.stop or args.stop_all) else "Stopping"
    print(f"{action} {len(filtered)} responder(s):")
    for proc in filtered:
        print("  " + format_responder(proc))

    if args.dry_run:
        return

    if args.stop or args.stop_all:
        for proc in filtered:
            proc.stop()
        print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
