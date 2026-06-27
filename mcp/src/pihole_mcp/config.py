"""Runtime configuration loaded from environment + .env file."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-wide config. All values come from env or .env."""

    pihole_url: str = Field(default="http://127.0.0.1:8081")
    pihole_app_password: str = Field(default="")

    mcp_bearer_token: str = Field(default="")
    mcp_host: str = Field(default="127.0.0.1")
    mcp_port: int = Field(default=8473)
    mcp_path: str = Field(default="/mcp")
    mcp_allowed_origins: str = Field(default="*")

    log_level: str = Field(default="INFO")
    audit_log_path: str = Field(default="/var/log/pihole-mcp/audit.log")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("pihole_url")
    @classmethod
    def _validate_pihole_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("PIHOLE_URL must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("PIHOLE_URL must include a host")
        return v.rstrip("/")

    @field_validator("mcp_path")
    @classmethod
    def _validate_mcp_path(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("MCP_PATH must start with '/'")
        return v

    @field_validator("mcp_port")
    @classmethod
    def _validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("MCP_PORT must be between 1 and 65535")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        u = v.upper()
        if u not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return u

    @property
    def allowed_origins_list(self) -> list[str]:
        raw = self.mcp_allowed_origins.strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
