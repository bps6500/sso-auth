"""Public API for sso_auth package."""

from .core import (
    authenticate,
    cli_main,
    create_session,
    display_results,
    get_user_info,
    save_results,
    try_auth_code_flow,
    try_direct_grant,
    try_session_based,
)

__all__ = [
    "authenticate",
    "cli_main",
    "create_session",
    "display_results",
    "get_user_info",
    "save_results",
    "try_auth_code_flow",
    "try_direct_grant",
    "try_session_based",
]
