from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_name: str = "Hubstaff MCP"

    # Transport: "stdio" (default, for local MCP clients) or "http" (self-hosting).
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    # Hubstaff Personal Access Token (acts as a long-lived, rotating refresh token).
    hubstaff_personal_access_token: str = ""
    hubstaff_token_store: Path = Path.home() / ".hubstaff-mcp" / "tokens.json"
    hubstaff_api_base: str = "https://api.hubstaff.com/v2"
    hubstaff_token_url: str = "https://account.hubstaff.com/access_tokens"

    default_timezone: str = "UTC"
    page_limit: int = 100

    @field_validator("default_timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"Invalid default_timezone {value!r}; use an IANA name like 'UTC' or 'Europe/Warsaw'"
            ) from exc
        return value

    @field_validator("mcp_transport")
    @classmethod
    def _validate_transport(cls, value: str) -> str:
        allowed = {"stdio", "http"}
        if value not in allowed:
            raise ValueError(f"Invalid mcp_transport {value!r}; choose one of {sorted(allowed)}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
