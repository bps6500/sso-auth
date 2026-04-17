"""Smart hybrid login for Playwright browser sessions.

Strategy:
1. Load storage_state.json into browser context (if it exists).
2. Navigate to the target app URL.
3. If the browser ends up on an SSO login page (redirect to sso_host) → auto-fill
   Keycloak credentials and submit.
4. Save the updated storage_state after a successful login.

This means subsequent runs skip step 3 entirely until the session expires.
"""

from __future__ import annotations

import getpass
from typing import TYPE_CHECKING

from sso_auth.exceptions import AuthError
from sso_auth.logging import get_logger

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from sso_auth.client import SsoClient

log = get_logger(__name__)

# Keycloak login form selectors (consistent with auth/code_flow.py).
_USERNAME_SELECTOR = "#username, input[name='username']"
_PASSWORD_SELECTOR = "#password, input[name='password']"
_SUBMIT_SELECTOR = "button[type='submit'], input[type='submit']"


def smart_login(
    page: "Page",
    client: "SsoClient",
    app_url: str,
    sso_host: str,
    timeout: int = 30_000,
) -> bool:
    """Navigate to app_url and login via SSO if the session is not already valid.

    Returns True if a fresh UI login was performed, False if storage_state was
    sufficient and no login form was encountered.

    Raises AuthError if login is attempted but the browser does not redirect back
    to the application within `timeout` ms.
    """
    log.info("Navigating to %s", app_url)
    page.goto(app_url, wait_until="domcontentloaded", timeout=timeout)

    if sso_host not in page.url:
        log.info("Existing session valid — no login required")
        return False

    log.info("Redirected to SSO login page — performing auto UI login")
    return _auto_ui_login(page, client, app_url, sso_host, timeout)


def _auto_ui_login(
    page: "Page",
    client: "SsoClient",
    app_url: str,
    sso_host: str,
    timeout: int = 30_000,
) -> bool:
    """Fill and submit the Keycloak login form, then wait for redirect back to app."""
    password = client.password or getpass.getpass(
        f"Password for {client.username} (not cached): "
    )

    # Wait for the login form to be visible before interacting.
    page.wait_for_selector(_USERNAME_SELECTOR, timeout=timeout)

    page.fill(_USERNAME_SELECTOR, client.username)
    page.fill(_PASSWORD_SELECTOR, password)
    page.click(_SUBMIT_SELECTOR)

    try:
        page.wait_for_url(
            lambda url: sso_host not in url,
            timeout=timeout,
        )
    except Exception as exc:
        # Check for error message on the SSO page.
        error_el = page.query_selector(".alert-error, #input-error, .kc-feedback-text")
        detail = error_el.inner_text() if error_el else "unknown reason"
        raise AuthError(f"SSO login failed: {detail}") from exc

    log.info("Login successful — now on %s", page.url)
    return True
