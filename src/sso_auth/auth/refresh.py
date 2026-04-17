"""Refresh-token flow."""

from __future__ import annotations

import requests

from sso_auth.config import Settings
from sso_auth.exceptions import NetworkError, TokenExpiredError
from sso_auth.models import TokenBundle


def refresh_access_token(
    session: requests.Session,
    refresh_token: str,
    client_id: str,
    settings: Settings,
) -> TokenBundle:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if client_id == settings.confidential_client and settings.client_secret:
        payload["client_secret"] = settings.client_secret
    try:
        resp = session.post(settings.token_url, data=payload)
    except requests.RequestException as exc:
        raise NetworkError(str(exc)) from exc

    if resp.status_code == 200:
        return TokenBundle.from_token_response(resp.json(), client_id=client_id)
    try:
        body = resp.json()
    except ValueError:
        body = {}
    if body.get("error") == "invalid_grant":
        raise TokenExpiredError("Refresh token invalid or expired")
    raise NetworkError(f"Refresh failed with status {resp.status_code}")
