"""
Integration CLI test scaffolding: shared fixtures.
"""

from pathlib import Path
import os
import pytest


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure IPC env vars don't leak between tests."""
    for key in [
        "IPC_SHARED_SECRET",
        "IPC_PORT",
        "IPC_HOST",
    ]:
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    return d
"""Integration CLI tests shared fixtures.

Placeholder for future project/broker fixtures.
"""
