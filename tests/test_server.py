from fastmcp import Client

from app.config import settings
from app.main import mcp


def test_server_uses_configured_name():
    assert mcp.name == settings.mcp_server_name


async def test_server_lists_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert len(tools) >= 1
