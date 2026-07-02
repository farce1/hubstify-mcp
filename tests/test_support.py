import pytest
from fastmcp.exceptions import ToolError

from app.hubstaff.errors import HubstaffError
from app.mcp.support import bullet_list, hours, safe


async def test_safe_raises_tool_error_for_hubstaff_error():
    @safe
    async def boom() -> str:
        raise HubstaffError("api down")

    with pytest.raises(ToolError, match="api down"):
        await boom()


async def test_safe_raises_tool_error_for_value_error():
    @safe
    async def boom() -> str:
        raise ValueError("bad input")

    with pytest.raises(ToolError, match="bad input"):
        await boom()


async def test_safe_passes_through_success():
    @safe
    async def ok() -> str:
        return "fine"

    assert await ok() == "fine"


def test_bullet_list_uses_empty_message_when_no_lines():
    assert bullet_list("Header:", [], "Nothing here.") == "Nothing here."


def test_bullet_list_formats_lines():
    assert bullet_list("Header:", ["a", "b"], "empty") == "Header:\n- a\n- b"


def test_hours_is_human_readable():
    assert hours(9000) == "2h 30m"
