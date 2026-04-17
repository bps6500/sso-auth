"""Browser automation helpers for sso_auth.

Install extras before use:
    pip install sso-auth[browser]
    playwright install chromium

Submodules that do not use Playwright directly (human, login, storage) are
importable without Playwright installed.  BrowserSession and stealth helpers
require Playwright and will raise a clear ImportError if it is missing.
"""

from __future__ import annotations

from sso_auth.browser.human import HumanBehavior


def __getattr__(name: str):  # noqa: ANN001
    if name == "BrowserSession":
        try:
            from sso_auth.browser.session import BrowserSession  # noqa: PLC0415
            return BrowserSession
        except ImportError as exc:
            raise ImportError(
                "sso_auth.browser.BrowserSession requires Playwright.\n"
                "Install it with:  pip install sso-auth[browser] && playwright install chromium"
            ) from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["BrowserSession", "HumanBehavior"]
