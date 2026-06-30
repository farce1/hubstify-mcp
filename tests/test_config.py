import pytest
from pydantic import ValidationError

from app.config import Settings


def test_valid_timezone_accepted():
    assert Settings(default_timezone="Europe/Warsaw").default_timezone == "Europe/Warsaw"


def test_invalid_timezone_rejected():
    with pytest.raises(ValidationError, match="default_timezone"):
        Settings(default_timezone="Not/AZone")


def test_valid_transport_accepted():
    assert Settings(mcp_transport="http").mcp_transport == "http"


def test_invalid_transport_rejected():
    with pytest.raises(ValidationError, match="mcp_transport"):
        Settings(mcp_transport="grpc")
