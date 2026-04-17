"""Session-cookie fallback authentication flow."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from sso_auth.auth.code_flow import _get_login_form
from sso_auth.config import Settings
from sso_auth.logging import get_logger
from sso_auth.models import AuthResult, UserInfo

log = get_logger(__name__)


def _cookie_jar_to_flat_dict(jar: requests.cookies.RequestsCookieJar) -> dict[str, str]:
    out: dict[str, str] = {}
    for cookie in jar:
        out[cookie.name] = cookie.value
    return out


def try_session_based(session: requests.Session, username: str, password: str, settings: Settings) -> AuthResult | None:
    action_url = _get_login_form(session, settings.confidential_client, settings)
    if not action_url:
        return None

    session.post(action_url, data={"username": username, "password": password}, allow_redirects=True)
    all_cookies = _cookie_jar_to_flat_dict(session.cookies)
    if not all_cookies:
        return None

    kc_cookies = {
        k: v
        for k, v in all_cookies.items()
        if "KEYCLOAK" in k.upper() or "AUTH_SESSION" in k.upper() or "KC_" in k.upper()
    }
    userinfo: dict = {}

    ui_resp = session.get(settings.userinfo_url)
    if ui_resp.status_code == 200:
        userinfo = ui_resp.json()

    if not userinfo:
        account_url = f"{settings.sso_base_url}/auth/realms/{settings.realm}/account"
        acc_resp = session.get(account_url)
        if acc_resp.status_code == 200:
            try:
                userinfo = acc_resp.json()
            except ValueError:
                soup = BeautifulSoup(acc_resp.text, "html.parser")
                for script in soup.find_all("script"):
                    if script.string and "userName" in script.string:
                        match = re.search(r'"userName"\s*:\s*"([^"]+)"', script.string)
                        if match:
                            userinfo["preferred_username"] = match.group(1)
                            break
    log.info("Session-based flow succeeded with %d cookies", len(all_cookies))
    return AuthResult(
        method="session_cookies",
        cookies=all_cookies,
        keycloak_cookies=kc_cookies,
        user_info=UserInfo.from_payload(userinfo) if userinfo else None,
    )
