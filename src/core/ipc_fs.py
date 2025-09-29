from __future__ import annotations

from pathlib import Path


def project_ipc_root(project_root: Path) -> Path:
    return project_root / ".ipc"


def ensure_ipc_layout(project_root: Path) -> dict[str, Path]:
    """Create .ipc/{config,logs,state,secret} layout if missing.
    Stub: create paths only; no content yet.
    """
    ipc = project_ipc_root(project_root)
    paths = {
        "root": ipc,
        "config": ipc / "config",
        "logs": ipc / "logs",
        "state": ipc / "state",
        "secret": ipc / "secret",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths
