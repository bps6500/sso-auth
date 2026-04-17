"""High level SSO client facade."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

from sso_auth.auth.code_flow import create_session
from sso_auth.auth.refresh import refresh_access_token
from sso_auth.auth.session_flow import try_session_based
from sso_auth.auth import try_auth_code_flow
from sso_auth.config import Settings
from sso_auth.exceptions import AuthError, NoRefreshTokenError
from sso_auth.models import AuthResult, TokenBundle, UserInfo
from sso_auth.storage.cookies import load_cookies, save_cookies
from sso_auth.storage.keyring_backend import (
    delete_all,
    get_password,
    get_refresh_token,
    save_password,
    save_refresh_token,
)
from sso_auth.storage.state import load_state, save_state


class SsoClient:
    """Facade for login/refresh/session lifecycle."""

    def __init__(
        self,
        username: str,
        password: str | None = None,
        use_keyring: bool = False,
        settings: Settings | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.use_keyring = use_keyring
        self.settings = settings or Settings()
        self._session = create_session()
        self._token_bundle: TokenBundle | None = None
        self._user_info: UserInfo | None = None
        self._callbacks: list[Callable[[TokenBundle], None]] = []

    @classmethod
    def from_keyring(cls, username: str, settings: Settings | None = None) -> "SsoClient":
        password = get_password(username)
        client = cls(username=username, password=password, use_keyring=True, settings=settings)
        refresh = get_refresh_token(username)
        if refresh:
            client._token_bundle = TokenBundle(access_token="", refresh_token=refresh, expires_in=0)
        state = load_state(client.settings.state_dir)
        if state.get("token"):
            client._token_bundle = TokenBundle.model_validate(state["token"])
        if state.get("user_info"):
            client._user_info = UserInfo.model_validate(state["user_info"])
        client._session.cookies.update(load_cookies(client.settings.state_dir))
        return client

    def on_token_refresh(self, callback: Callable[[TokenBundle], None]) -> None:
        self._callbacks.append(callback)

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def access_token(self) -> str:
        if not self._token_bundle:
            return ""
        return self._token_bundle.access_token

    @property
    def refresh_token(self) -> str:
        if not self._token_bundle or not self._token_bundle.refresh_token:
            return ""
        return self._token_bundle.refresh_token

    @property
    def user_info(self) -> UserInfo | None:
        return self._user_info

    @property
    def is_authenticated(self) -> bool:
        return bool(self._token_bundle and self._token_bundle.access_token)

    def _persist(self) -> None:
        payload: dict[str, Any] = {}
        if self._token_bundle:
            payload["token"] = self._token_bundle.model_dump(mode="json", exclude_none=True)
        if self._user_info:
            payload["user_info"] = self._user_info.model_dump(exclude_none=True)
        save_state(self.settings.state_dir, payload)
        save_cookies(self.settings.state_dir, self._session.cookies)
        if self._token_bundle and self._token_bundle.refresh_token:
            save_refresh_token(self.username, self._token_bundle.refresh_token)

    def login(self) -> AuthResult:
        if not self.password and self.use_keyring:
            self.password = get_password(self.username)
        if not self.password:
            raise AuthError("Password is required")

        result = try_auth_code_flow(self._session, self.username, self.password, self.settings)
        if result is None:
            result = try_session_based(self._session, self.username, self.password, self.settings)
        if result is None:
            raise AuthError("All authentication methods failed")

        self._token_bundle = result.tokens
        self._user_info = result.user_info
        self._persist()
        if self.use_keyring and self.password:
            save_password(self.username, self.password)
        return result

    def refresh(self) -> TokenBundle:
        if not self._token_bundle or not self._token_bundle.refresh_token:
            raise NoRefreshTokenError("No refresh token available")
        client_id = self._token_bundle.client_id or self.settings.confidential_client
        refreshed = refresh_access_token(self._session, self._token_bundle.refresh_token, client_id, self.settings)
        self._token_bundle = refreshed
        self._persist()
        for callback in self._callbacks:
            callback(refreshed)
        return refreshed

    def ensure_valid(self, skew: int = 60) -> None:
        if not self._token_bundle:
            self.login()
            return
        if self._token_bundle.is_expiring(skew_seconds=skew):
            self.refresh()

    def logout(self) -> None:
        delete_all(self.username)
        self._token_bundle = None
        self._user_info = None
        save_state(self.settings.state_dir, {})

