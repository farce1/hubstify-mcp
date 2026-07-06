import pytest
from pydantic import ValidationError

from app.config import Settings


def test_valid_transport_accepted():
    assert Settings(mcp_transport="http").mcp_transport == "http"


def test_invalid_transport_rejected():
    with pytest.raises(ValidationError, match="mcp_transport"):
        Settings(mcp_transport="grpc")
