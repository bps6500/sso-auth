"""Playwright storage_state persistence.

storage_state.json holds browser cookies, localStorage, and sessionStorage so
that subsequent runs skip the login UI and reuse an existing authenticated session.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext

from sso_auth.config import Settings


def default_storage_path(settings: Settings) -> Path:
    """Return the default path for the Playwright storage_state file."""
    return settings.state_dir / "storage_state.json"


def load_storage(path: Path) -> dict[str, Any] | None:
    """Load a storage_state dict from disk, or return None if missing/corrupt."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def save_storage(context: "BrowserContext", path: Path) -> None:
    """Persist the current browser context state to disk for future reuse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(path))


def clear_storage(path: Path) -> None:
    """Remove the storage_state file to force a fresh login next run."""
    if path.exists():
        path.unlink()
