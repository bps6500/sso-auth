"""Unit tests for browser storage_state persistence helpers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sso_auth.browser.storage import clear_storage, load_storage, save_storage


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_load_storage_returns_none_when_missing(tmp_dir: Path) -> None:
    result = load_storage(tmp_dir / "nonexistent.json")
    assert result is None


def test_load_storage_returns_none_for_corrupt_file(tmp_dir: Path) -> None:
    bad = tmp_dir / "bad.json"
    bad.write_text("not { valid json", encoding="utf-8")
    assert load_storage(bad) is None


def test_load_storage_returns_dict_for_valid_file(tmp_dir: Path) -> None:
    path = tmp_dir / "state.json"
    payload = {"cookies": [{"name": "kc", "value": "abc"}], "origins": []}
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = load_storage(path)
    assert result == payload


def test_load_storage_returns_none_for_non_dict_json(tmp_dir: Path) -> None:
    path = tmp_dir / "list.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert load_storage(path) is None


def test_save_storage_calls_context_storage_state(tmp_dir: Path) -> None:
    mock_context = MagicMock()
    path = tmp_dir / "sub" / "state.json"
    save_storage(mock_context, path)
    mock_context.storage_state.assert_called_once_with(path=str(path))
    assert path.parent.exists()


def test_clear_storage_removes_file(tmp_dir: Path) -> None:
    path = tmp_dir / "state.json"
    path.write_text("{}", encoding="utf-8")
    assert path.exists()
    clear_storage(path)
    assert not path.exists()


def test_clear_storage_is_noop_when_missing(tmp_dir: Path) -> None:
    clear_storage(tmp_dir / "missing.json")  # should not raise
