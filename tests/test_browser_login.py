"""Unit tests for smart_login branching logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sso_auth.browser.login import _auto_ui_login, smart_login
from sso_auth.exceptions import AuthError


def _make_client(username: str = "user", password: str = "pass") -> MagicMock:
    client = MagicMock()
    client.username = username
    client.password = password
    return client


def _make_page(url: str = "https://app.bps.go.id/dashboard") -> MagicMock:
    page = MagicMock()
    page.url = url
    page.goto.return_value = None
    page.wait_for_url.return_value = None
    page.fill.return_value = None
    page.click.return_value = None
    page.wait_for_selector.return_value = None
    page.query_selector.return_value = None
    return page


class TestSmartLogin:
    def test_no_login_when_session_valid(self) -> None:
        """Storage state is valid: browser lands on app, no SSO form shown."""
        page = _make_page(url="https://app.bps.go.id/dashboard")
        client = _make_client()
        result = smart_login(page, client, "https://app.bps.go.id/", "sso.bps.go.id")
        assert result is False
        page.fill.assert_not_called()

    def test_login_performed_when_redirected_to_sso(self) -> None:
        """Browser redirects to SSO → auto UI login should be triggered."""
        page = _make_page(url="https://sso.bps.go.id/auth/realms/pegawai-bps/login")
        client = _make_client()
        with patch("sso_auth.browser.login._auto_ui_login", return_value=True) as mock_login:
            result = smart_login(page, client, "https://app.bps.go.id/", "sso.bps.go.id")
        assert result is True
        mock_login.assert_called_once()

    def test_goto_called_with_app_url(self) -> None:
        page = _make_page(url="https://app.bps.go.id/home")
        client = _make_client()
        smart_login(page, client, "https://app.bps.go.id/home", "sso.bps.go.id")
        page.goto.assert_called_once_with(
            "https://app.bps.go.id/home",
            wait_until="domcontentloaded",
            timeout=30_000,
        )


class TestAutoUiLogin:
    def test_fills_and_clicks_form(self) -> None:
        page = _make_page()
        client = _make_client()
        _auto_ui_login(page, client, "https://app.bps.go.id/", "sso.bps.go.id")
        page.fill.assert_any_call("#username, input[name='username']", "user")
        page.fill.assert_any_call("#password, input[name='password']", "pass")
        page.click.assert_called_once()
        page.wait_for_url.assert_called_once()

    def test_raises_auth_error_on_timeout(self) -> None:
        page = _make_page()
        client = _make_client()
        page.wait_for_url.side_effect = Exception("Timeout")
        with pytest.raises(AuthError, match="SSO login failed"):
            _auto_ui_login(page, client, "https://app.bps.go.id/", "sso.bps.go.id")

    def test_includes_error_message_from_page(self) -> None:
        page = _make_page()
        client = _make_client()
        page.wait_for_url.side_effect = Exception("Timeout")
        error_el = MagicMock()
        error_el.inner_text.return_value = "Invalid credentials"
        page.query_selector.return_value = error_el
        with pytest.raises(AuthError, match="Invalid credentials"):
            _auto_ui_login(page, client, "https://app.bps.go.id/", "sso.bps.go.id")
