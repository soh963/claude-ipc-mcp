from __future__ import annotations

from tests.helpers.cli import run_ipc


def test_ipc_chat_minimal_contract(temp_project):
    init = run_ipc(["init"], cwd=temp_project)
    assert init.returncode == 0

    # Without a running broker peer, we expect graceful handling or local echo in early implementation
    proc = run_ipc(["chat", "--to", "self", "hello"], cwd=temp_project)

    # For first red stage, just assert the command exists and returns a code (may be non-zero initially)
    assert proc.returncode in (0, 12)  # 12: message delivery failed per contract
    out = (proc.stdout or "") + (proc.stderr or "")
    assert any(k in out.lower() for k in ["correlation", "message", "delivered", "failed", "echo"])  # loose check
