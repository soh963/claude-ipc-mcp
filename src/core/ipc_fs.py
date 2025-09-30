"""Filesystem helpers for project-local `.ipc` structure.

Creates and resolves project-scoped `.ipc/` layout:
- .ipc/
  - config/config.yaml (default stub if missing)
  - logs/
  - state/.sentinel (created if missing)
  - secret/secrets.env (default stub if missing)

All operations are idempotent and safe to call multiple times.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict


def project_root(start: Path | None = None) -> Path:
    """Return the project root (defaults to current working directory)."""
    return (start or Path.cwd()).resolve()


def project_ipc_root(root: Path | None = None) -> Path:
    return project_root(root) / ".ipc"


def config_dir(root: Path | None = None) -> Path:
    return project_ipc_root(root) / "config"


def logs_dir(root: Path | None = None) -> Path:
    return project_ipc_root(root) / "logs"


def state_dir(root: Path | None = None) -> Path:
    return project_ipc_root(root) / "state"


def secret_dir(root: Path | None = None) -> Path:
    return project_ipc_root(root) / "secret"


def ensure_ipc_layout(root: Path | None = None) -> Dict[str, Path]:
    """Ensure `.ipc` layout exists and write default files if absent.

    Returns a mapping with useful paths.
    """
    ipc = project_ipc_root(root)
    cfg = config_dir(root)
    logs = logs_dir(root)
    state = state_dir(root)
    secret = secret_dir(root)

    # Create directories idempotently
    for p in (ipc, cfg, logs, state, secret):
        p.mkdir(parents=True, exist_ok=True)

    # Default files (only if missing)
    config_file = cfg / "config.yaml"
    if not config_file.exists():
        config_file.write_text(
            "# IPC project configuration\nversion: 0\n# add settings under this key\nsettings: {}\n",
            encoding="utf-8",
        )

    secrets_file = secret / "secrets.env"
    if not secrets_file.exists():
        secrets_file.write_text(
            "# Secrets for IPC project (dotenv format)\n# IPC_SHARED_SECRET=\n",
            encoding="utf-8",
        )

    sentinel = state / ".sentinel"
    if not sentinel.exists():
        sentinel.write_text("initialized\n", encoding="utf-8")

    return {
        "root": ipc,
        "config": cfg,
        "logs": logs,
        "state": state,
        "secret": secret,
        "config_file": config_file,
        "secrets_file": secrets_file,
        "state_sentinel": sentinel,
    }
