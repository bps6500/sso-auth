"""Authorization code flow implementation."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from sso_auth.config import Settings
from sso_auth.exceptions import NetworkError
from sso_auth.logging import get_logger
from sso_auth.models import AuthResult, TokenBundle

log = get_logger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )
    return session


def get_redirect_uri(client_id: str, settings: Settings) -> str:
    redirect_map = {
        "account": f"{settings.sso_base_url}/auth/realms/{settings.realm}/account/login-redirect",
        "account-console": f"{settings.sso_base_url}/auth/realms/{settings.realm}/account/",
        "security-admin-console": f"{settings.sso_base_url}/auth/admin/{settings.realm}/console/",
        "admin-cli": f"{settings.sso_base_url}/auth/realms/{settings.realm}/account/",
        "broker": f"{settings.sso_base_url}/auth/realms/{settings.realm}/broker/",
    }
    return redirect_map.get(client_id, f"{settings.sso_base_url}/auth/realms/{settings.realm}/account/")


def _get_login_form(session: requests.Session, client_id: str, settings: Settings) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": get_redirect_uri(client_id, settings),
        "response_type": "code",
        "scope": "openid",
    }
    try:
        resp = session.get(settings.auth_url, params=params, allow_redirects=True)
    except requests.RequestException as exc:
        raise NetworkError(str(exc)) from exc
    if resp.status_code != 200:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", id="kc-form-login") or soup.find("form")
    if not form or not form.get("action"):
        return ""
    return str(form["action"])


def _submit_credentials(session: requests.Session, action_url: str, username: str, password: str) -> str:
    resp = session.post(action_url, data={"username": username, "password": password}, allow_redirects=False)
    for _ in range(10):
        if resp.status_code not in (301, 302, 303, 307, 308):
            break
        location = resp.headers.get("Location", "")
        query = parse_qs(urlparse(location).query)
        if "code" in query:
            return query["code"][0]
        if "error" in query:
            return ""
        resp = session.get(location, allow_redirects=False)
    return ""


def try_auth_code_flow(session: requests.Session, username: str, password: str, settings: Settings) -> AuthResult | None:
    clients = list(settings.client_id_preferences)
    if settings.client_secret:
        clients.append(settings.confidential_client)

    for client_id in clients:
        trial = create_session()
        log.info("Trying auth code flow using client_id=%s", client_id)
        action_url = _get_login_form(trial, client_id, settings)
        if not action_url:
            continue
        code = _submit_credentials(trial, action_url, username, password)
        if not code:
            continue
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": get_redirect_uri(client_id, settings),
            "code": code,
        }
        if client_id == settings.confidential_client and settings.client_secret:
            payload["client_secret"] = settings.client_secret
        resp = trial.post(settings.token_url, data=payload)
        if resp.status_code == 200:
            token = TokenBundle.from_token_response(resp.json(), client_id=client_id)
            session.cookies.update(trial.cookies)
            return AuthResult(method="auth_code", client_id=client_id, tokens=token)
    return None
