import pytest
from pydantic import ValidationError

from app.config import Settings


def test_valid_transport_accepted():
    assert Settings(mcp_transport="http").mcp_transport == "http"


def test_invalid_transport_from_env_rejected(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "grpc")
    with pytest.raises(ValidationError, match="mcp_transport"):
        Settings()
