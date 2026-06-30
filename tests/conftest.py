import httpx
import pytest

from app.hubstaff.client import HubstaffClient
from app.mcp import context as context_module
from tests._helpers import BASE


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
