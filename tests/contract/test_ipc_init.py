from pathlib import Path
from tests.helpers.cli import run_ipc


def test_ipc_init_creates_layout(temp_project):
    code = run_ipc(["init"], cwd=temp_project).returncode
    assert code == 0
    for sub in ("config", "logs", "state", "secret"):
        assert (Path(temp_project) / ".ipc" / sub).exists()


def test_ipc_init_idempotent(temp_project):
    first = run_ipc(["init"], cwd=temp_project)
    second = run_ipc(["init"], cwd=temp_project)
    assert first.returncode == 0 and second.returncode == 0
