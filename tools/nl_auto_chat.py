#!/usr/bin/env python3
"""Natural language wrapper for IPC chat demos."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
KNOWN_AGENTS = ["codex", "gemini", "chatgpt", "lm", "llama"]


def run_command(args: List[str]) -> None:
    subprocess.run(args, cwd=str(REPO_ROOT), check=True)


def run_quick_chat(agent_a: str, agent_b: str, message: str, timeout: int, monitor: bool) -> None:
    cmd = [
        PYTHON,
        str(TOOLS_DIR / "chat_once.py"),
        agent_a,
        agent_b,
        message,
        "--timeout",
        str(timeout),
        "--auto-responder",
    ]
    if monitor:
        cmd.append("--monitor")
    run_command(cmd)


def run_continuous_chat(agent_a: str, agent_b: str, message: str, duration: int, max_turns: int) -> None:
    tokens = message.split()
    cmd = [
        PYTHON,
        str(TOOLS_DIR / "auto_chat_demo.py"),
        agent_a,
        agent_b,
        "--message",
        *tokens,
        "--duration",
        str(duration),
        "--max-turns",
        str(max_turns),
    ]
    run_command(cmd)


def extract_agents(prompt: str) -> Tuple[str, str]:
    found: List[str] = []
    lowered = prompt.lower()
    for name in KNOWN_AGENTS:
        if name in lowered and name not in found:
            found.append(name)
    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        partner = "gemini" if found[0] != "gemini" else "codex"
        return found[0], partner
    return "codex", "gemini"


def extract_message(prompt: str) -> str:
    quoted = re.findall(r"[\"']([^\"']+)[\"']", prompt)
    if quoted:
        return quoted[0]

    tokens = prompt.split()
    for idx, token in enumerate(tokens):
        if "메시지" in token:
            start = max(0, idx - 1)
            candidate = " ".join(tokens[start:idx + 1])
            candidate = candidate.replace("메시지를", "메시지").replace("메시지로", "메시지")
            return candidate.strip()

    match = re.search(r"(?:메시지|말해|전달|message|send)\s*(?:를|을|해|해줘|:)?\s*(.+)", prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Hello from the natural language interface!"


def extract_duration(prompt: str) -> int:
    match = re.search(r"(\d+)\s*초", prompt)
    if match:
        return max(5, int(match.group(1)))
    match = re.search(r"(\d+)\s*분", prompt)
    if match:
        return max(30, int(match.group(1)) * 60)
    return 30


def extract_turns(prompt: str) -> int:
    match = re.search(r"(\d+)\s*(?:턴|회|responses?)", prompt)
    if match:
        return max(2, int(match.group(1)))
    return 12


def wants_monitoring(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in ["모니터", "live", "실시간", "monitor"])


def determine_mode(prompt: str) -> str:
    lowered = prompt.lower()
    if any(keyword in lowered for keyword in ["계속", "지속", "long", "conversation", "연속"]):
        return "continuous"
    return "quick"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch an IPC chat using natural language instructions.")
    parser.add_argument("prompt", nargs="+", help="Natural language description of the desired chat flow.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show interpreted parameters without executing any chat.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> None:
    args = parse_args(argv)
    prompt = " ".join(args.prompt)

    agent_a, agent_b = extract_agents(prompt)
    message = extract_message(prompt)
    duration = extract_duration(prompt)
    max_turns = extract_turns(prompt)
    monitor = wants_monitoring(prompt)
    mode = determine_mode(prompt)

    print("[NL-CLI] Parsed parameters")
    print(f"  mode       : {mode}")
    print(f"  agent_a    : {agent_a}")
    print(f"  agent_b    : {agent_b}")
    print(f"  message    : {message}")
    print(f"  duration   : {duration}s")
    print(f"  max_turns  : {max_turns}")
    print(f"  monitoring : {monitor}")
    sys.stdout.flush()

    if args.dry_run:
        return

    if mode == "continuous":
        run_continuous_chat(agent_a, agent_b, message, duration, max_turns)
    else:
        timeout = min(duration, 60)
        run_quick_chat(agent_a, agent_b, message, timeout, monitor)


if __name__ == "__main__":
    main(sys.argv[1:])
