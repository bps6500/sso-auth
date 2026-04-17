"""Cookie jar persistence."""

from __future__ import annotations

import pickle
from pathlib import Path

import requests


def _cookie_file(state_dir: Path) -> Path:
    return state_dir / "cookies.pickle"


def save_cookies(state_dir: Path, jar: requests.cookies.RequestsCookieJar) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    _cookie_file(state_dir).write_bytes(pickle.dumps(jar))


def load_cookies(state_dir: Path) -> requests.cookies.RequestsCookieJar:
    path = _cookie_file(state_dir)
    if not path.exists():
        return requests.cookies.RequestsCookieJar()
    return pickle.loads(path.read_bytes())
