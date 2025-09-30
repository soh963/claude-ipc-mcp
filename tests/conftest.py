import shutil
import tempfile
from pathlib import Path
import contextlib
import sys
import os

# Ensure our repository's src/ is importable before any similarly named external packages
try:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    SRC_PATH = REPO_ROOT / "src"
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
except Exception:
    pass

import pytest


@contextlib.contextmanager
def _temp_project_dir(prefix: str = "ipc-proj-"):
    d = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
def temp_project():
    with _temp_project_dir() as d:
        yield d
