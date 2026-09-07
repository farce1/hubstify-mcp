from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_name: str = "Hubstaff MCP"

    # Transport: "stdio" (default, for local MCP clients) or "http" (self-hosting).
    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    # Hubstaff Personal Access Token (acts as a long-lived, rotating refresh token).
    hubstaff_personal_access_token: str = ""
    hubstaff_token_store: Path = Path.home() / ".hubstaff-mcp" / "tokens.json"
    hubstaff_api_base: str = "https://api.hubstaff.com/v2"
    hubstaff_token_url: str = "https://account.hubstaff.com/access_tokens"
    # Organization used when a tool isn't given one. Defaults to the first one returned.
    hubstaff_default_organization_id: int | None = None


settings = Settings()
