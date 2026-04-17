from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sso_auth.cli import app
from sso_auth.client import SsoClient
from sso_auth.exceptions import NoRefreshTokenError
from sso_auth.models import AuthResult, TokenBundle


def test_client_refresh_requires_token() -> None:
    client = SsoClient(username="u", password="p")
    with pytest.raises(NoRefreshTokenError):
        client.refresh()


def test_client_ensure_valid_triggers_refresh(settings) -> None:
    client = SsoClient(username="u", password="p", settings=settings)
    client._token_bundle = TokenBundle(access_token="a", refresh_token="r", expires_in=0)
    with patch("sso_auth.client.refresh_access_token") as mocked_refresh, patch(
        "sso_auth.client.save_refresh_token"
    ):
        mocked_refresh.return_value = TokenBundle(access_token="new", refresh_token="newr", expires_in=3600)
        client.ensure_valid()
        assert mocked_refresh.called


def test_cli_token_subcommand() -> None:
    runner = CliRunner()

    class _DummyClient:
        access_token = "dummy-token"

        def ensure_valid(self):
            return None

    with patch("sso_auth.cli._build_client", return_value=_DummyClient()):
        result = runner.invoke(app, ["token", "fachri"])
        assert result.exit_code == 0
        assert "dummy-token" in result.output


def test_client_login_fallback_session_flow(settings) -> None:
    client = SsoClient(username="u", password="p", settings=settings)
    with patch("sso_auth.client.try_auth_code_flow", return_value=None), patch(
        "sso_auth.client.try_session_based", return_value=AuthResult(method="session_cookies")
    ):
        result = client.login()
        assert result.method == "session_cookies"
