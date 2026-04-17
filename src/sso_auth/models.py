"""Typed data models used by sso_auth."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """Normalized user information from SSO endpoints."""

    sub: str | None = None
    email: str | None = None
    name: str | None = None
    username: str | None = None
    preferred_username: str | None = None
    roles: list[str] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UserInfo":
        realm_roles = payload.get("realm_access", {}).get("roles", [])
        return cls(
            sub=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name") or payload.get("firstName"),
            username=payload.get("username"),
            preferred_username=payload.get("preferred_username"),
            roles=list(realm_roles) if isinstance(realm_roles, list) else [],
        )


class TokenBundle(BaseModel):
    """Token payload returned from Keycloak token endpoint."""

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 0
    refresh_expires_in: int | None = None
    scope: str | None = None
    session_state: str | None = None
    client_id: str | None = None
    expires_at: datetime | None = None

    @classmethod
    def from_token_response(cls, payload: dict[str, Any], client_id: str | None = None) -> "TokenBundle":
        expires_in = int(payload.get("expires_in") or 0)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return cls(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            id_token=payload.get("id_token"),
            token_type=payload.get("token_type", "bearer"),
            expires_in=expires_in,
            refresh_expires_in=payload.get("refresh_expires_in"),
            scope=payload.get("scope"),
            session_state=payload.get("session_state"),
            client_id=client_id,
            expires_at=expires_at,
        )

    def is_expiring(self, skew_seconds: int = 60) -> bool:
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) + timedelta(seconds=skew_seconds) >= self.expires_at


class AuthResult(BaseModel):
    """Result object for login attempts."""

    method: str
    client_id: str | None = None
    tokens: TokenBundle | None = None
    cookies: dict[str, str] | None = None
    keycloak_cookies: dict[str, str] | None = None
    user_info: UserInfo | None = None

    def to_legacy_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"_method": self.method}
        if self.client_id:
            data["_client_id"] = self.client_id
        if self.tokens:
            data.update(self.tokens.model_dump(mode="json", exclude_none=True))
        if self.cookies:
            data["_cookies"] = self.cookies
        if self.keycloak_cookies:
            data["_keycloak_cookies"] = self.keycloak_cookies
        if self.user_info:
            data["user_info"] = self.user_info.model_dump(exclude_none=True)
        return data
