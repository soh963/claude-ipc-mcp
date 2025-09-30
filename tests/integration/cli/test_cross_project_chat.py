from __future__ import annotations

from pathlib import Path
import pytest

from tests.helpers.cli import run_ipc


def test_cross_project_chat_delivery(tmp_path_factory: pytest.TempPathFactory):
    # Create two separate projects A and B
    a: Path = tmp_path_factory.mktemp("proj-a")
    b: Path = tmp_path_factory.mktemp("proj-b")

    # Initialize both projects
    r1 = run_ipc(["init"], cwd=a)
    assert r1.returncode == 0
    r2 = run_ipc(["init"], cwd=b)
    assert r2.returncode == 0

    # Attempt to send a message from A to B
    msg = "hello from A to B"
    r3 = run_ipc(["chat", "--to", b.name, msg], cwd=a)
    # Expect delivered if broker routing works; else fallback echo would fail this test
    assert r3.returncode == 0
    out = (r3.stdout or "") + (r3.stderr or "")
    assert ("to=" + b.name) in out and "delivered" in out
