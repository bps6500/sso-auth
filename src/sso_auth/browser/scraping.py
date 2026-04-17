"""Scraping and download helpers for Playwright pages."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page

from sso_auth.logging import get_logger

log = get_logger(__name__)


def download_to(
    page: "Page",
    target_path: Path,
    trigger_selector: str | None = None,
    trigger_url: str | None = None,
    timeout: int = 60_000,
) -> Path:
    """Trigger a file download and save it to target_path.

    Provide either ``trigger_selector`` (CSS selector to click) or
    ``trigger_url`` (URL to navigate to that initiates the download directly).
    Returns the resolved target_path after the file is saved.

    Raises ValueError if neither trigger is provided.
    """
    if trigger_selector is None and trigger_url is None:
        raise ValueError("Provide either trigger_selector or trigger_url.")

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with page.expect_download(timeout=timeout) as dl_info:
        if trigger_selector:
            page.click(trigger_selector)
        else:
            page.goto(trigger_url)  # type: ignore[arg-type]

    download = dl_info.value
    tmp = download.path()
    if tmp:
        shutil.copy(tmp, target_path)
        download.delete()
        log.info("Downloaded to %s", target_path)
    else:
        # Playwright already saved in suggested location; move it.
        suggested = download.suggested_filename
        if suggested:
            target_path = target_path.parent / suggested
        download.save_as(str(target_path))
        log.info("Saved download to %s", target_path)

    return target_path


def extract_table(page: "Page", table_selector: str = "table") -> list[dict[str, Any]]:
    """Extract an HTML table into a list of dicts keyed by column headers.

    Reads the first matching ``<table>`` element.  Header names are taken from
    ``<thead> <th>`` cells; rows from ``<tbody> <tr>``.

    Returns an empty list if the selector matches nothing or the table has no
    header row.
    """
    table = page.query_selector(table_selector)
    if table is None:
        return []

    headers: list[str] = [
        th.inner_text().strip()
        for th in table.query_selector_all("thead th, thead td")
    ]
    if not headers:
        # Fallback: first row as headers when no <thead>.
        first_row = table.query_selector("tr:first-child")
        if first_row is None:
            return []
        headers = [td.inner_text().strip() for td in first_row.query_selector_all("th, td")]

    rows: list[dict[str, Any]] = []
    for tr in table.query_selector_all("tbody tr"):
        cells = [td.inner_text().strip() for td in tr.query_selector_all("td")]
        if cells:
            rows.append(dict(zip(headers, cells)))

    return rows


def wait_any(
    page: "Page",
    selectors: list[str],
    timeout: int = 30_000,
) -> str:
    """Wait for the first selector in the list to appear and return which one.

    Useful for waiting after an action that may result in either a success
    element or an error element (e.g., successful redirect vs login error).

    Raises TimeoutError if none of the selectors appear within timeout.
    """
    js_conditions = " || ".join(
        f"document.querySelector({repr(s)})" for s in selectors
    )
    page.wait_for_function(js_conditions, timeout=timeout)

    for selector in selectors:
        if page.query_selector(selector) is not None:
            return selector

    raise TimeoutError(f"None of the selectors found: {selectors}")
