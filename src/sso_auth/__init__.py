"""Public API for sso_auth package."""

from .client import SsoClient
from .exceptions import AuthError, InvalidCredentialsError, NetworkError, NoRefreshTokenError, TokenExpiredError
from .models import AuthResult, TokenBundle, UserInfo
from .core import authenticate, cli_main, create_session, display_results, get_user_info, save_results

__all__ = [
    "SsoClient",
    "AuthResult",
    "TokenBundle",
    "UserInfo",
    "AuthError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "NetworkError",
    "NoRefreshTokenError",
    "authenticate",
    "cli_main",
    "create_session",
    "display_results",
    "get_user_info",
    "save_results",
]
