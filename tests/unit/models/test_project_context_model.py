from __future__ import annotations

from pathlib import Path

from src.core.models.project_context import ProjectIPCContext


def test_project_ipc_context_build(tmp_path: Path):
    root = tmp_path / "My Project!#"
    root.mkdir()
    ctx = ProjectIPCContext.build(root)
    # project id sanitized
    assert ctx.project_id.startswith("My-Project-") or ctx.project_id == "project"
    # paths resolved
    assert ctx.root == root.resolve()
    assert ctx.ipc_dir == root.resolve() / ".ipc"
    assert ctx.config_dir == ctx.ipc_dir / "config"
    assert ctx.logs_dir == ctx.ipc_dir / "logs"
    assert ctx.state_dir == ctx.ipc_dir / "state"
    assert ctx.secret_dir == ctx.ipc_dir / "secret"
    assert ctx.responders == []
