"""Non-secret state persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _state_file(state_dir: Path) -> Path:
    return state_dir / "state.json"


def save_state(state_dir: Path, payload: dict[str, Any]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    _state_file(state_dir).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state(state_dir: Path) -> dict[str, Any]:
    path = _state_file(state_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
