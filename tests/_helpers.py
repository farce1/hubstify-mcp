import respx
from fastmcp import Client
from httpx import Response

from app.main import mcp

BASE = "https://api.hubstaff.com/v2"


async def call_tool(tool: str, args: dict | None = None) -> str:
    async with Client(mcp) as client:
        result = await client.call_tool(tool, args or {})
    return result.content[0].text


def mock_me(user_id: int = 7, name: str = "Jo"):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": user_id, "name": name}}))


def mock_projects(org_id: int = 9, projects=None):
    rows = projects if projects is not None else [{"id": 1, "name": "Acme"}]
    respx.get(f"{BASE}/organizations/{org_id}/projects").mock(
        return_value=Response(200, json={"projects": rows, "pagination": {}}),
    )
