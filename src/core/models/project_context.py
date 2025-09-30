from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ProjectIPCContext:
    project_id: str
    root: Path
    ipc_dir: Path
    config_dir: Path
    logs_dir: Path
    state_dir: Path
    secret_dir: Path
    responders: List[str]

    @staticmethod
    def build(root: Path) -> "ProjectIPCContext":
        r = root.resolve()
        ipc = r / ".ipc"
        cfg = ipc / "config"
        logs = ipc / "logs"
        state = ipc / "state"
        secret = ipc / "secret"
        # project id from folder name (sanitized like default_instance_id)
        import re

        pid = re.sub(r"[^a-zA-Z0-9_-]", "-", r.name)[:32] or "project"
        return ProjectIPCContext(
            project_id=pid,
            root=r,
            ipc_dir=ipc,
            config_dir=cfg,
            logs_dir=logs,
            state_dir=state,
            secret_dir=secret,
            responders=[],
        )
