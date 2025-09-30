from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ResponderProcess:
    instance_id: str
    pid: Optional[int]
    pid_file: Path
    started_at: Optional[str] = None
    last_response_at: Optional[str] = None
    last_check_at: Optional[str] = None
    policy: Optional[str] = None


def _data_dirs() -> Path:
    return Path(os.path.expandvars(r"%USERPROFILE%\.claude-ipc-data"))


def _pid_file(instance_id: str) -> Path:
    base = _data_dirs() / "responders"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{instance_id}.pid"


def _status_file(instance_id: str) -> Path:
    base = _data_dirs() / "responders"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{instance_id}.json"


def is_running(instance_id: str) -> bool:
    pf = _pid_file(instance_id)
    if not pf.exists():
        return False
    try:
        pid = int(pf.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        # Check with tasklist
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        return str(pid) in (out.stdout or "")
    else:
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False


def start(instance_id: str, policy: str = "simple", detach: bool = False) -> ResponderProcess:
    script = Path(__file__).resolve().parents[2] / "tools" / "auto_responder.py"
    if not script.exists():
        raise FileNotFoundError(f"auto_responder.py not found at {script}")
    env = os.environ.copy()
    env["IPC_INSTANCE_ID"] = instance_id
    if policy:
        env["IPC_RESPONDER_POLICY"] = policy
    pid_path = _pid_file(instance_id)
    if is_running(instance_id):
        # Return existing
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            pid = None
        meta = _read_status_meta(instance_id)
        return ResponderProcess(
            instance_id,
            pid,
            pid_path,
            started_at=meta.get("started_at"),
            last_response_at=meta.get("last_response_at"),
            last_check_at=meta.get("last_check_at"),
            policy=meta.get("policy"),
        )

    creationflags = 0
    popen_kwargs = {}
    if os.name == "nt":
        # CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
        creationflags = 0x00000200 | 0x00000008
        popen_kwargs["creationflags"] = creationflags
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.DEVNULL if detach else None,
        stderr=subprocess.DEVNULL if detach else None,
        env=env,
        **popen_kwargs,
    )
    try:
        pid_path.write_text(str(proc.pid), encoding="utf-8")
    except Exception:
        pass
    # Try to read initial metadata (may appear shortly after startup)
    meta = _read_status_meta(instance_id)
    return ResponderProcess(
        instance_id,
        proc.pid,
        pid_path,
        started_at=meta.get("started_at"),
        last_response_at=meta.get("last_response_at"),
        last_check_at=meta.get("last_check_at"),
        policy=meta.get("policy", policy),
    )


def stop(instance_id: str) -> bool:
    pf = _pid_file(instance_id)
    if not pf.exists():
        return True
    try:
        pid = int(pf.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        pid = 0
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        else:
            import signal
            if pid > 0:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        try:
            pf.unlink()
        except Exception:
            pass
        # Remove status file as well (best-effort)
        try:
            _status_file(instance_id).unlink()
        except Exception:
            pass
        return True
    except Exception:
        return False


def get_info(instance_id: str) -> ResponderProcess:
    pf = _pid_file(instance_id)
    pid = None
    if pf.exists():
        try:
            pid = int(pf.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            pid = None
    meta = _read_status_meta(instance_id)
    return ResponderProcess(
        instance_id,
        pid,
        pf,
        started_at=meta.get("started_at"),
        last_response_at=meta.get("last_response_at"),
        last_check_at=meta.get("last_check_at"),
        policy=meta.get("policy"),
    )


def _read_status_meta(instance_id: str) -> dict:
    """Read status metadata JSON written by auto_responder (best-effort)."""
    try:
        sf = _status_file(instance_id)
        if sf.exists():
            import json

            return json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}
