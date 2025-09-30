#!/usr/bin/env python3
"""Automated IPC conversation runner with live monitoring."""
from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable


def run_command(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        check=True,
        text=True,
        capture_output=True,
    )


def ensure_broker() -> None:
    result = run_command([PYTHON, str(TOOLS_DIR / "start_broker.py")])
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


def ensure_registration(instance: str) -> None:
    session_file = Path.home() / f".ipc-session-{instance}"
    result = run_command([PYTHON, str(TOOLS_DIR / "ipc_register.py"), instance, "--no-default"])
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if not session_file.exists():
        raise RuntimeError(f"Session file missing for {instance}: {session_file}")


def launch_responder(instance: str) -> subprocess.Popen:
    print(f"📡 Launching auto-responder for {instance}...")
    return subprocess.Popen(
        [PYTHON, str(TOOLS_DIR / "simple_auto_responder.py"), instance],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def stream_output(proc: subprocess.Popen, label: str, turn_counter: dict[str, int]) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        text = line.rstrip()
        print(f"[{label}] {text}")
        if "Sent to" in text:
            turn_counter[label] = turn_counter.get(label, 0) + 1
    proc.stdout.close()


def send_message(sender: str, recipient: str, content: str) -> None:
    result = run_command(
        [
            PYTHON,
            str(TOOLS_DIR / "ipc_send.py"),
            "--instance",
            sender,
            recipient,
            content,
        ]
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an automated IPC chat demo with live monitoring."
    )
    parser.add_argument(
        "agent_a", nargs="?", default="codex", help="First agent name (default: codex)"
    )
    parser.add_argument(
        "agent_b", nargs="?", default="gemini", help="Second agent name (default: gemini)"
    )
    parser.add_argument(
        "--message",
        nargs="+",
        default=["Hello", "from", "the", "automation", "demo!"],
        help="Initial message to send from agent_a to agent_b.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Conversation length in seconds before auto shutdown (default: 30).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=12,
        help="Maximum replies per agent before stopping (default: 12).",
    )
    return parser.parse_args(list(argv))


def terminate_process(proc: Optional[subprocess.Popen]) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def main(argv: Iterable[str]) -> None:
    args = parse_args(argv)
    initial_message = " ".join(args.message)

    print("======= IPC Auto Chat Demo =======")
    print(f"Agents        : {args.agent_a}, {args.agent_b}")
    print(f"Initial message: {initial_message}")
    print(f"Duration       : {args.duration}s")
    print(f"Max turns      : {args.max_turns}")
    print("==================================\n")

    ensure_broker()
    ensure_registration(args.agent_a)
    ensure_registration(args.agent_b)

    responder_a = launch_responder(args.agent_a)
    responder_b = launch_responder(args.agent_b)

    turn_counter: dict[str, int] = {args.agent_a: 0, args.agent_b: 0}

    threads = [
        threading.Thread(
            target=stream_output,
            args=(responder_a, args.agent_a, turn_counter),
            daemon=True,
        ),
        threading.Thread(
            target=stream_output,
            args=(responder_b, args.agent_b, turn_counter),
            daemon=True,
        ),
    ]
    for t in threads:
        t.start()

    time.sleep(2)
    send_message(args.agent_a, args.agent_b, initial_message)

    print("\nConversation running. Ctrl+C to stop early.\n")

    start_time = time.time()
    try:
        while time.time() - start_time < args.duration:
            if all(turn_counter.get(agent, 0) >= args.max_turns for agent in turn_counter):
                print("Max turn limit reached. Stopping chat.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping chat...")
    finally:
        terminate_process(responder_a)
        terminate_process(responder_b)
        print("Clean exit.")


if __name__ == "__main__":
    main(sys.argv[1:])
