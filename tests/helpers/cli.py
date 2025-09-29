from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


def run_ipc(args: List[str], cwd: Path | None = None):
    """
    Run the repo's global IPC command via Python entrypoint to avoid PATH issues.
    Prefer 'python tools/ipc_global_command.py' for portability across shells.
    Returns CompletedProcess.
    """
    cmd = [
        "python",
        str(Path(__file__).resolve().parents[2] / "tools" / "ipc_global_command.py"),
        *args,
    ]
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
