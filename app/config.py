from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_name: str = "Hubstaff MCP"

    # Hubstaff Personal Access Token (acts as a long-lived, rotating refresh token).
    hubstaff_refresh_token: str = ""
    hubstaff_token_store: Path = Path.home() / ".hubstaff-mcp" / "tokens.json"
    hubstaff_api_base: str = "https://api.hubstaff.com/v2"
    hubstaff_token_url: str = "https://account.hubstaff.com/access_tokens"

    default_timezone: str = "UTC"
    page_limit: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
