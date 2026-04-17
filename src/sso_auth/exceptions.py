"""Custom exceptions for sso_auth."""


class AuthError(Exception):
    """Base error for authentication failures."""


class InvalidCredentialsError(AuthError):
    """Username/password rejected by identity provider."""


class TokenExpiredError(AuthError):
    """Refresh token no longer valid."""


class NetworkError(AuthError):
    """Network request to auth service failed."""


class NoRefreshTokenError(AuthError):
    """Refresh was requested without refresh token."""
