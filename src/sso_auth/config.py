"""Runtime settings for sso_auth."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings with sane defaults."""

    model_config = SettingsConfigDict(env_prefix="SSO_", extra="ignore")

    sso_base_url: str = "https://sso.bps.go.id"
    realm: str = "pegawai-bps"
    client_id_preferences: list[str] = Field(
        default_factory=lambda: [
            "account-console",
            "security-admin-console",
            "admin-cli",
            "broker",
        ]
    )
    confidential_client: str = "account"
    client_secret: str = ""
    state_dir: Path = Path("~/.config/sso-auth").expanduser()

    @property
    def auth_url(self) -> str:
        return f"{self.sso_base_url}/auth/realms/{self.realm}/protocol/openid-connect/auth"

    @property
    def token_url(self) -> str:
        return f"{self.sso_base_url}/auth/realms/{self.realm}/protocol/openid-connect/token"

    @property
    def userinfo_url(self) -> str:
        return f"{self.sso_base_url}/auth/realms/{self.realm}/protocol/openid-connect/userinfo"
