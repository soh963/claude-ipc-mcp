"""
Contract test scaffolding: shared minimal fixtures.
"""

from pathlib import Path
import os
import pytest


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Provide an isolated temporary project directory.

    Keeps contract tests self-contained and avoids touching the repo root.
    """
    d = tmp_path / "project"
    d.mkdir()
    return d
"""Contract tests shared fixtures.

Currently minimal; temp path fixtures from pytest are used per-test.
"""


@pytest.fixture(autouse=True)
def _restore_cwd_between_tests():
    """Ensure each test leaves the process CWD unchanged.

    Some tests chdir into a temp directory; this restores the original CWD
    after each test so later tests (that expect repo-root relative paths)
    aren't impacted.
    """
    old = os.getcwd()
    try:
        yield
    finally:
        try:
            os.chdir(old)
        except Exception:
            pass
