from __future__ import annotations

import json
import time
from pathlib import Path

# Core imports (available in this project)
# from core.project_context import ensure_layout  # no longer used; kept for reference
from core import broker_client


def ensure_broker() -> None:
    """Ensure the TCP broker is running; if not, start it in-process and wait briefly."""
    # Prefer core helper if available
    try:
        if hasattr(broker_client, "ensure_broker_running"):
            broker_client.ensure_broker_running(1.0)
            return
    except Exception:
        pass
    # Fallback to legacy inline behavior
    try:
        resp = broker_client.status()
        if resp.get("status") == "ok":
            return
    except Exception:
        pass
    try:
        import importlib

        importlib.import_module("claude_ipc_server")
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
    """Create minimal .ipc layout and required files to satisfy contracts."""
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
        cfg_json.write_text(json.dumps({"version": "1.0.0", "min_compatible_version": "1.0.0"}))
        created.append(str(cfg_json))
    proj_state = ipc_root / "state" / "project.json"
    if not proj_state.exists():
        # Contract expects project_id to start with 'proj_'
        proj_id = f"proj_{project_dir.name}"
        proj_state.write_text(json.dumps({"project_id": proj_id}))
        created.append(str(proj_state))
    gitignore = ipc_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            (
                """
config/*
secret/*
logs/*
state/*
!config/
!logs/
!state/
!secret/
"""
            ).strip()
        )
        created.append(str(gitignore))
    return {"project_dir": str(project_dir), "ipc_root": str(ipc_root), "created": created}


def read_project_id(cwd: Path) -> str | None:
    try:
        st_path = cwd / ".ipc" / "state" / "project.json"
        if st_path.exists():
            st = json.loads(st_path.read_text())
            return st.get("project_id") or st.get("projectId")
    except Exception:
        return None
    return None


def get_cli_version(default: str = "2.0.0") -> str:
    try:
        import importlib.metadata

        return importlib.metadata.version("claude-ipc-mcp")
    except Exception:
        return default
