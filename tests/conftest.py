import httpx
import pytest
import respx
from fastmcp import Client
from httpx import Response

from app.hubstaff.client import HubstaffClient
from app.main import mcp
from app.mcp import context as context_module

BASE = "https://api.hubstaff.com/v2"


class StaticTokens:
    async def get_access_token(self) -> str:
        return "test-token"

    async def force_refresh(self, stale: str) -> str:
        return "test-token"


async def _noop_sleep(seconds: float) -> None:
    return None


@pytest.fixture
async def api():
    async with httpx.AsyncClient() as http:
        yield HubstaffClient(http=http, tokens=StaticTokens(), base_url=BASE, sleep=_noop_sleep)


@pytest.fixture(autouse=True)
def _reset_context(monkeypatch):
    # Guarantee no leaked global Context (which would build a real networked client).
    monkeypatch.setattr(context_module, "_context", None)


@pytest.fixture
def tool_context(api, monkeypatch):
    context = context_module.Context(api)
    monkeypatch.setattr(context_module, "_context", context)
    return context


async def call_tool(tool: str, args: dict | None = None) -> str:
    async with Client(mcp) as client:
        result = await client.call_tool(tool, args or {})
    return result.content[0].text


def mock_me(user_id: int = 7, name: str = "Jo", time_zone: str | None = None):
    user = {"id": user_id, "name": name}
    if time_zone is not None:
        user["time_zone"] = time_zone
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": user}))


def mock_projects(org_id: int = 9, projects=None):
    rows = projects if projects is not None else [{"id": 1, "name": "Acme"}]
    respx.get(f"{BASE}/organizations/{org_id}/projects").mock(
        return_value=Response(200, json={"projects": rows, "pagination": {}}),
    )
