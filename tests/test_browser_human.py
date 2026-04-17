"""Unit tests for HumanBehavior timing helpers."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from sso_auth.browser.human import HumanBehavior


def test_pause_within_jitter_range() -> None:
    hb = HumanBehavior(jitter=(0.05, 0.10))
    start = time.monotonic()
    hb.pause()
    elapsed = time.monotonic() - start
    assert 0.05 <= elapsed <= 0.30, f"pause duration {elapsed:.3f}s out of expected range"


def test_short_pause_is_shorter_than_pause() -> None:
    hb = HumanBehavior(jitter=(0.8, 1.5))
    with patch("sso_auth.browser.human.time") as mock_time, \
         patch("sso_auth.browser.human.random") as mock_random:
        mock_random.uniform.return_value = 1.0
        hb.pause()
        mock_time.sleep.assert_called_with(1.0)


def test_type_into_calls_keyboard_for_each_char() -> None:
    hb = HumanBehavior(type_delay=(10.0, 20.0))
    mock_page = MagicMock()
    text = "hello"
    with patch("sso_auth.browser.human.random") as mock_random:
        mock_random.uniform.return_value = 15.0
        hb.type_into(mock_page, "#field", text)

    mock_page.click.assert_called_once_with("#field")
    assert mock_page.keyboard.type.call_count == len(text)
    for call, ch in zip(mock_page.keyboard.type.call_args_list, text):
        assert call.args[0] == ch
        assert call.kwargs["delay"] == 15.0


def test_default_jitter_range_is_valid() -> None:
    hb = HumanBehavior()
    lo, hi = hb.jitter
    assert lo < hi
    lo_t, hi_t = hb.type_delay
    assert lo_t < hi_t
