"""Lightweight browser fingerprint patches via Playwright init scripts.

These patches are injected into every page context before any page script runs.
They align the headless Chromium fingerprint with a typical desktop Chrome browser
without relying on external stealth libraries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext

# Chrome version to impersonate – update periodically.
CHROME_VERSION = "124.0.0.0"
USER_AGENT = (
    f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    f"AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_VERSION} Safari/537.36"
)

_STEALTH_SCRIPT = """
// Remove the automation indicator
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Minimal plugins list (empty in headless, desktop has several)
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' },
    ],
});

// Consistent languages with id-ID locale
Object.defineProperty(navigator, 'languages', { get: () => ['id-ID', 'id', 'en-US', 'en'] });

// Make window.chrome exist (headless Chromium omits it)
if (!window.chrome) {
    window.chrome = { runtime: {} };
}

// Consistent platform
Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });

// Prevent permission query automation fingerprint
const _origQuery = window.navigator.permissions?.query;
if (_origQuery) {
    window.navigator.permissions.query = (params) =>
        params.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : _origQuery.call(window.navigator.permissions, params);
}
"""


def apply_patches(context: BrowserContext) -> None:
    """Inject fingerprint patches and set realistic context metadata."""
    context.add_init_script(_STEALTH_SCRIPT)
    # Locale and timezone are set at context creation; re-affirm via extra HTTP headers.
    context.set_extra_http_headers(
        {
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": (
                f'"Chromium";v="{CHROME_VERSION.split(".")[0]}", '
                f'"Google Chrome";v="{CHROME_VERSION.split(".")[0]}", '
                '"Not.A/Brand";v="99"'
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }
    )
