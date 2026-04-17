"""BrowserSession: high-level sync context manager for authenticated headless browsing."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from sso_auth.browser.login import smart_login
from sso_auth.browser.stealth import CHROME_VERSION, USER_AGENT, apply_patches
from sso_auth.browser.storage import (
    clear_storage,
    default_storage_path,
    load_storage,
    save_storage,
)
from sso_auth.logging import get_logger

if TYPE_CHECKING:
    from sso_auth.browser.human import HumanBehavior
    from sso_auth.client import SsoClient

log = get_logger(__name__)

_DEFAULT_VIEWPORT = {"width": 1366, "height": 768}


class BrowserSession:
    """Sync context manager that wraps a Playwright Browser/Context/Page lifecycle.

    Usage::

        from sso_auth import SsoClient
        from sso_auth.browser import BrowserSession

        client = SsoClient.from_keyring("username")
        with BrowserSession.launch(client, app_url="https://app.bps.go.id/") as b:
            b.page.goto("https://app.bps.go.id/laporan")
            b.download_to("/tmp/laporan.xlsx", trigger_selector="#btn-export")

    On ``__exit__`` the storage_state is automatically saved so the next run
    skips the login form entirely.
    """

    def __init__(
        self,
        browser: Browser,
        context: BrowserContext,
        page: Page,
        storage_path: Path,
        human: "HumanBehavior | None" = None,
    ) -> None:
        self._pw_browser = browser
        self._context = context
        self._page = page
        self._storage_path = storage_path
        self._human = human
        self._pw = None  # held by launch() classmethod

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def launch(
        cls,
        client: "SsoClient",
        app_url: str,
        headless: bool = True,
        storage_path: Path | None = None,
        stealth: bool = True,
        human: "HumanBehavior | None" = None,
        timeout: int = 30_000,
    ) -> "BrowserSession":
        """Launch a browser, apply patches, perform smart login, and return a session.

        This is the main entry point.  The returned object is a context manager.
        """
        from sso_auth.browser.human import HumanBehavior  # avoid circular at module level

        if human is None:
            human = HumanBehavior()

        resolved_storage = storage_path or default_storage_path(client.settings)
        existing_state = load_storage(resolved_storage)
        sso_host = urlparse(client.settings.sso_base_url).netloc

        pw_ctx = sync_playwright().start()

        browser = pw_ctx.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context_kwargs: dict[str, Any] = {
            "viewport": _DEFAULT_VIEWPORT,
            "user_agent": USER_AGENT,
            "locale": "id-ID",
            "timezone_id": "Asia/Jakarta",
            "extra_http_headers": {
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        }
        if existing_state:
            context_kwargs["storage_state"] = existing_state

        context = browser.new_context(**context_kwargs)

        if stealth:
            apply_patches(context)

        page = context.new_page()

        session = cls(
            browser=browser,
            context=context,
            page=page,
            storage_path=resolved_storage,
            human=human,
        )
        session._pw = pw_ctx

        did_login = smart_login(page, client, app_url, sso_host, timeout=timeout)
        if did_login:
            save_storage(context, resolved_storage)
            log.info("storage_state saved to %s", resolved_storage)

        return session

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "BrowserSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            save_storage(self._context, self._storage_path)
        except Exception:
            pass
        try:
            self._context.close()
        except Exception:
            pass
        try:
            self._pw_browser.close()
        except Exception:
            pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def page(self) -> Page:
        return self._page

    @property
    def context(self) -> BrowserContext:
        return self._context

    @property
    def browser(self) -> Browser:
        return self._pw_browser

    # ------------------------------------------------------------------
    # Action helpers
    # ------------------------------------------------------------------

    def click(self, selector: str, human: bool = True) -> None:
        """Click an element, optionally with a human-like pause beforehand."""
        if human and self._human:
            self._human.pause()
        self._page.click(selector)

    def fill(self, selector: str, value: str, human: bool = True) -> None:
        """Fill a form field, optionally with per-character typing delay."""
        if human and self._human:
            self._human.type_into(self._page, selector, value)
        else:
            self._page.fill(selector, value)

    def wait_for(self, selector: str, timeout: int = 30_000) -> None:
        self._page.wait_for_selector(selector, timeout=timeout)

    def screenshot(self, path: str | Path) -> None:
        self._page.screenshot(path=str(path), full_page=True)

    def download_to(
        self,
        target_path: str | Path,
        trigger_selector: str | None = None,
        trigger_url: str | None = None,
    ) -> Path:
        """Trigger a file download and save it to target_path.

        Provide either ``trigger_selector`` (a CSS selector to click) or
        ``trigger_url`` (a URL to navigate to that initiates the download).
        Returns the resolved target path.
        """
        from sso_auth.browser.scraping import download_to as _download_to

        return _download_to(
            self._page,
            target_path=Path(target_path),
            trigger_selector=trigger_selector,
            trigger_url=trigger_url,
        )
