"""Human-like timing helpers to reduce automation detection via cadence analysis."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


class HumanBehavior:
    """Inject realistic timing into browser interactions.

    Parameters
    ----------
    jitter:
        (min_sec, max_sec) random sleep range between page-level actions.
    type_delay:
        (min_ms, max_ms) per-character typing delay in milliseconds.
    """

    def __init__(
        self,
        jitter: tuple[float, float] = (0.6, 2.2),
        type_delay: tuple[float, float] = (40.0, 130.0),
    ) -> None:
        self.jitter = jitter
        self.type_delay = type_delay

    def pause(self) -> None:
        """Sleep for a random interval that mimics human reaction time."""
        time.sleep(random.uniform(*self.jitter))

    def short_pause(self) -> None:
        """Brief pause between small sub-actions (e.g., between fields)."""
        time.sleep(random.uniform(0.15, 0.45))

    def type_into(self, page: "Page", selector: str, text: str) -> None:
        """Type text character-by-character with random per-key delay.

        This avoids the clipboard-paste pattern that automation detectors flag.
        The element is clicked first to mimic natural focus acquisition.
        """
        page.click(selector)
        self.short_pause()
        for ch in text:
            page.keyboard.type(ch, delay=random.uniform(*self.type_delay))
