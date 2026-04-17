from __future__ import annotations

import pytest
import requests
import responses

from sso_auth.auth.refresh import refresh_access_token
from sso_auth.exceptions import TokenExpiredError


@responses.activate
def test_refresh_success(settings):
    responses.post(
        settings.token_url,
        json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600},
        status=200,
    )
    token = refresh_access_token(requests.Session(), "old-refresh", "account-console", settings)
    assert token.access_token == "new-access"
    assert token.refresh_token == "new-refresh"


@responses.activate
def test_refresh_invalid_grant(settings):
    responses.post(settings.token_url, json={"error": "invalid_grant"}, status=400)
    with pytest.raises(TokenExpiredError):
        refresh_access_token(requests.Session(), "expired", "account-console", settings)
