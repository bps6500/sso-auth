"""Logging helpers for sso_auth."""

from __future__ import annotations

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_default_logging(level: int = logging.INFO) -> None:
    """Configure default stream logging for CLI use."""
    root = logging.getLogger("sso_auth")
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get module logger namespaced under sso_auth."""
    if not name.startswith("sso_auth"):
        name = f"sso_auth.{name}"
    return logging.getLogger(name)
