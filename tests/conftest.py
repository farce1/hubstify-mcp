import httpx
import pytest

from app.hubstaff.client import HubstaffClient

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
