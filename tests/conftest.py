from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sso_auth.config import Settings


@pytest.fixture
def settings() -> Settings:
    with tempfile.TemporaryDirectory() as tmp:
        yield Settings(state_dir=Path(tmp), client_secret="")
