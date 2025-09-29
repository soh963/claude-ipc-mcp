#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure 'src' is importable for local development
SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Prefer core modules if available
try:
    from core.project_context import ensure_layout, read_session, write_session, default_instance_id
    from core import broker_client
    _core_available = True
except Exception:
    ensure_layout = None
    read_session = None
    write_session = None
    default_instance_id = None
    broker_client = None
    _core_available = False


def ensure_broker() -> None:
    """Ensure the TCP broker is running; if not, start it in-process and wait briefly."""
    if not _core_available:
        return
    try:
        resp = broker_client.status()
        if resp.get("status") == "ok":
            return
    except Exception:
        pass
    # Start embedded broker via claude_ipc_server import
    try:
        import importlib
        import time

        importlib.import_module("claude_ipc_server")
        # give it a moment to bind
        time.sleep(0.05)
    except Exception:
        pass


def ensure_ipc_layout(project_dir: Path) -> dict:
    ipc_root = project_dir / ".ipc"
    subdirs = ["config", "logs", "state", "secret"]
    created = []
    ipc_root.mkdir(exist_ok=True)
    for s in subdirs:
        p = ipc_root / s
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
    # we return a minimal status object
    return {"project_dir": str(project_dir), "ipc_root": str(ipc_root), "created": created}


def cmd_init(args: argparse.Namespace) -> int:
    ensure_ipc_layout(Path.cwd())
    # Optionally register to broker and persist session
    info = {"project_id": Path.cwd().name, "port": None}
    try:
        ensure_broker()
        if default_instance_id and broker_client and write_session:
            instance = default_instance_id(Path.cwd())
            resp = broker_client.register(instance)
            if resp.get("status") == "ok" and resp.get("session_token"):
                write_session(instance, resp["session_token"], Path.cwd())
                info.update({"instance_id": instance})
    except Exception:
        pass
    print(json.dumps(info))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    # Minimal JSON matching contract shape using broker client
    running = False
    connections = 0
    try:
        ensure_broker()
        if broker_client:
            resp = broker_client.status()
            running = resp.get("status") == "ok"
            connections = len(resp.get("instances", [])) if isinstance(resp.get("instances"), list) else 0
    except Exception:
        running = False
    data = {"broker": {"running": running, "version": None, "port": None}, "connections": connections, "last_ping_ms": None}
    print(json.dumps(data))
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    target = args.to or "local"
    rtt_ms = 0
    try:
        ensure_broker()
        if broker_client:
            sess = read_session() if read_session else None
            resp = broker_client.ping(session_token=sess.session_token if sess else None, target=target)
            rtt_ms = resp.get("rtt_ms", 0)
    except Exception:
        rtt_ms = 0
    print(f"pong ({target}) rtt_ms={rtt_ms}")
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    msg = " ".join(args.message) if args.message else ""
    target = args.to or "self"
    try:
        ensure_broker()
        if broker_client and read_session:
            sess = read_session()
            if sess and target not in ("self", "local"):
                resp = broker_client.send(sess.session_token, sess.instance_id, target, msg)
                status = resp.get("status")
                corr = f"corr-{abs(hash(msg)) % 100000}"
                if status == "ok":
                    print(f"to={target} correlation={corr} delivered")
                    return 0
                else:
                    print(f"to={target} correlation={corr} failed: {resp.get('message')}")
                    return 12
    except Exception as e:
        print(f"error: {e}")
        return 12
    # Fallback: local echo
    corr = f"corr-{abs(hash(msg)) % 100000}"
    print(f"to={target} correlation={corr} message={msg}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    # Very basic checks
    issues = []
    ipc_root = Path.cwd() / ".ipc"
    if not ipc_root.exists():
        issues.append(".ipc directory missing; run 'ipc init'")
    if issues:
        print("Detected issues:")
        for i in issues:
            print(f" - {i}")
    else:
        print("No critical issues detected.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ipc", description="Global IPC CLI (minimal)")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="Initialize project .ipc folder")
    sp.add_argument("--minimal", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("status", help="Show IPC status")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("ping", help="Ping broker or target project")
    sp.add_argument("--to", dest="to", default=None)
    sp.set_defaults(func=cmd_ping)

    sp = sub.add_parser("chat", help="Send a chat message")
    sp.add_argument("--to", dest="to", required=False)
    sp.add_argument("message", nargs=argparse.REMAINDER)
    sp.set_defaults(func=cmd_chat)

    sp = sub.add_parser("doctor", help="Diagnose IPC setup")
    sp.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())
