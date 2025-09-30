"""
Performance tests scaffolding.
"""

from pathlib import Path
import pytest


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    return d
