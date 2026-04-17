"""OS keyring persistence."""

from __future__ import annotations

import keyring

SERVICE_NAME = "sso.bps.go.id"


def save_password(username: str, password: str) -> None:
    keyring.set_password(SERVICE_NAME, f"{username}:password", password)


def get_password(username: str) -> str | None:
    return keyring.get_password(SERVICE_NAME, f"{username}:password")


def save_refresh_token(username: str, refresh_token: str) -> None:
    keyring.set_password(SERVICE_NAME, f"{username}:refresh_token", refresh_token)


def get_refresh_token(username: str) -> str | None:
    return keyring.get_password(SERVICE_NAME, f"{username}:refresh_token")


def delete_all(username: str) -> None:
    for suffix in ("password", "refresh_token"):
        try:
            keyring.delete_password(SERVICE_NAME, f"{username}:{suffix}")
        except Exception:
            continue
