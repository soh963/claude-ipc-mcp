import shutil
import tempfile
from pathlib import Path
import contextlib

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
