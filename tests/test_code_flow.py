from __future__ import annotations

import requests
import responses

from sso_auth.auth.code_flow import try_auth_code_flow


@responses.activate
def test_try_auth_code_flow_happy_path(settings):
    html = '<html><form id="kc-form-login" action="https://sso.bps.go.id/login_action"></form></html>'
    responses.get(settings.auth_url, body=html, status=200)
    responses.post(
        "https://sso.bps.go.id/login_action",
        status=302,
        headers={"Location": "https://redirect.local/cb?code=abc123"},
    )
    responses.post(
        settings.token_url,
        json={"access_token": "access", "refresh_token": "refresh", "expires_in": 3600},
        status=200,
    )
    result = try_auth_code_flow(requests.Session(), "u", "p", settings)
    assert result is not None
    assert result.method == "auth_code"
    assert result.tokens is not None
    assert result.tokens.access_token == "access"
