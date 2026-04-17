"""Backward-compatible wrappers around the new SDK API."""

from __future__ import annotations

import getpass
import json

import requests

from sso_auth.auth.code_flow import create_session
from sso_auth.client import SsoClient


def authenticate(username: str, password: str, session: requests.Session | None = None) -> dict:
    """Deprecated: use `SsoClient(...).login()`."""
    client = SsoClient(username=username, password=password)
    if session is not None:
        client._session = session
    result = client.login()
    return result.to_legacy_dict()


def get_user_info(session: requests.Session, access_token: str) -> dict:
    """Deprecated helper for retrieving userinfo endpoint."""
    resp = session.get(
        "https://sso.bps.go.id/auth/realms/pegawai-bps/protocol/openid-connect/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code == 200:
        return resp.json()
    return {}


def display_results(result: dict) -> None:
    """Deprecated display helper."""
    method = result.get("_method", "unknown")
    print(f"Metode: {method}")
    if "user_info" in result:
        print(f"Username: {result['user_info'].get('preferred_username', '-')}")
    if "access_token" in result:
        print(f"Access token: {result['access_token'][:50]}...")


def save_results(result: dict, filename: str = "sso_tokens.json") -> None:
    """Deprecated save helper."""
    output = {}
    for key, value in result.items():
        if not key.startswith("_") or key in ("_method", "_client_id"):
            output[key] = value
    if "_cookies" in result:
        output["cookies"] = result["_cookies"]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)


def cli_main() -> None:
    """Deprecated CLI entrypoint."""
    username = input("Username : ").strip()
    password = getpass.getpass("Password : ")
    result = authenticate(username, password)
    display_results(result)
