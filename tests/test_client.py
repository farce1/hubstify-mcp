import httpx
import pytest
import respx
from httpx import Response

from app.hubstaff.client import HubstaffClient
from app.hubstaff.errors import HubstaffAPIError, HubstaffRateLimitError

BASE = "https://api.hubstaff.com/v2"


class FakeTokens:
    def __init__(self):
        self.available = ["t1", "t2", "t3"]
        self.index = 0
        self.forced = 0

    async def get_access_token(self) -> str:
        return self.available[self.index]

    async def force_refresh(self, stale: str) -> str:
        self.index += 1
        self.forced += 1
        return self.available[self.index]


class SleepSpy:
    def __init__(self):
        self.calls = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def _client(http, *, tokens=None, sleep=None, max_retries=3):
    return HubstaffClient(
        http=http,
        tokens=tokens or FakeTokens(),
        base_url=BASE,
        sleep=sleep or SleepSpy(),
        max_retries=max_retries,
    )


@respx.mock
async def test_get_returns_json_with_bearer(tmp_path):
    route = respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 1}}))
    async with httpx.AsyncClient() as http:
        data = await _client(http).request("GET", "/users/me")
    assert data == {"user": {"id": 1}}
    assert route.calls.last.request.headers["Authorization"] == "Bearer t1"


@respx.mock
async def test_retries_once_after_401_refresh():
    route = respx.get(f"{BASE}/users/me").mock(side_effect=[Response(401), Response(200, json={"ok": True})])
    tokens = FakeTokens()
    async with httpx.AsyncClient() as http:
        data = await _client(http, tokens=tokens).request("GET", "/users/me")
    assert data == {"ok": True}
    assert tokens.forced == 1
    assert route.calls.last.request.headers["Authorization"] == "Bearer t2"


@respx.mock
async def test_persistent_401_raises_after_single_refresh():
    respx.get(f"{BASE}/users/me").mock(return_value=Response(401, json={"error": "unauthorized"}))
    tokens = FakeTokens()
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAPIError):
            await _client(http, tokens=tokens).request("GET", "/users/me")
    assert tokens.forced == 1


@respx.mock
async def test_429_honors_retry_after_then_succeeds():
    respx.get(f"{BASE}/x").mock(
        side_effect=[Response(429, headers={"Retry-After": "7"}), Response(200, json={"ok": 1})]
    )
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        data = await _client(http, sleep=spy).request("GET", "/x")
    assert data == {"ok": 1}
    assert spy.calls == [7.0]


@respx.mock
async def test_429_exhausted_raises_rate_limit_error():
    respx.get(f"{BASE}/x").mock(return_value=Response(429, headers={"Retry-After": "1"}))
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffRateLimitError):
            await _client(http, sleep=spy, max_retries=2).request("GET", "/x")
    assert len(spy.calls) == 2


@respx.mock
async def test_5xx_retries_with_exponential_backoff():
    respx.get(f"{BASE}/x").mock(side_effect=[Response(500), Response(503), Response(200, json={"ok": 1})])
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        data = await _client(http, sleep=spy, max_retries=3).request("GET", "/x")
    assert data == {"ok": 1}
    assert len(spy.calls) == 2
    assert spy.calls[1] > spy.calls[0]


@respx.mock
async def test_404_raises_without_retry():
    route = respx.get(f"{BASE}/x").mock(return_value=Response(404, json={"error": "not found"}))
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAPIError):
            await _client(http, sleep=spy).request("GET", "/x")
    assert spy.calls == []
    assert route.call_count == 1


@respx.mock
async def test_get_list_paginates_and_concatenates():
    route = respx.get(f"{BASE}/organizations/1/projects").mock(
        side_effect=[
            Response(200, json={"projects": [{"id": 1}], "pagination": {"next_page_start_id": 2}}),
            Response(200, json={"projects": [{"id": 2}], "pagination": {}}),
        ],
    )
    async with httpx.AsyncClient() as http:
        items = await _client(http).get_list("/organizations/1/projects", "projects")
    assert [i["id"] for i in items] == [1, 2]
    assert route.call_count == 2
    assert "page_start_id=2" in str(route.calls.last.request.url)


@respx.mock
async def test_empty_body_returns_none():
    respx.post(f"{BASE}/users/1/time_entries").mock(return_value=Response(201))
    async with httpx.AsyncClient() as http:
        data = await _client(http).request("POST", "/users/1/time_entries", json={"x": 1})
    assert data is None


@respx.mock
async def test_none_params_are_dropped():
    route = respx.get(f"{BASE}/x").mock(return_value=Response(200, json={}))
    async with httpx.AsyncClient() as http:
        await _client(http).request("GET", "/x", params={"a": 1, "b": None})
    url = str(route.calls.last.request.url)
    assert "a=1" in url
    assert "b=" not in url


@respx.mock
async def test_zero_and_false_params_are_kept():
    route = respx.get(f"{BASE}/x").mock(return_value=Response(200, json={}))
    async with httpx.AsyncClient() as http:
        await _client(http).request("GET", "/x", params={"a": 0, "b": False, "d": None})
    url = str(route.calls.last.request.url)
    assert "a=0" in url
    assert "b=false" in url
    assert "d=" not in url


@respx.mock
async def test_401_then_429_then_success():
    respx.get(f"{BASE}/x").mock(
        side_effect=[Response(401), Response(429, headers={"Retry-After": "2"}), Response(200, json={"ok": 1})],
    )
    tokens = FakeTokens()
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        data = await _client(http, tokens=tokens, sleep=spy).request("GET", "/x")
    assert data == {"ok": 1}
    assert tokens.forced == 1
    assert spy.calls == [2.0]


@respx.mock
async def test_exhausted_5xx_raises_api_error_not_rate_limit():
    respx.get(f"{BASE}/x").mock(return_value=Response(500, json={"error": "boom"}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAPIError) as exc:
            await _client(http, sleep=SleepSpy(), max_retries=1).request("GET", "/x")
    assert not isinstance(exc.value, HubstaffRateLimitError)


@respx.mock
async def test_get_list_requests_max_page_limit_by_default():
    route = respx.get(f"{BASE}/x").mock(return_value=Response(200, json={"items": [], "pagination": {}}))
    async with httpx.AsyncClient() as http:
        await _client(http).get_list("/x", "items")
    assert "page_limit=500" in str(route.calls.last.request.url)


@respx.mock
async def test_get_list_respects_page_limit_override():
    route = respx.get(f"{BASE}/x").mock(return_value=Response(200, json={"items": [], "pagination": {}}))
    async with httpx.AsyncClient() as http:
        await _client(http).get_list("/x", "items", params={"page_limit": 100})
    url = str(route.calls.last.request.url)
    assert "page_limit=100" in url
    assert "page_limit=500" not in url


@respx.mock
async def test_get_list_stops_on_cursor_cycle():
    respx.get(f"{BASE}/x").mock(
        side_effect=[
            Response(200, json={"items": [{"id": 1}], "pagination": {"next_page_start_id": 5}}),
            Response(200, json={"items": [{"id": 2}], "pagination": {"next_page_start_id": 9}}),
            Response(200, json={"items": [{"id": 3}], "pagination": {"next_page_start_id": 5}}),
        ],
    )
    async with httpx.AsyncClient() as http:
        items = await _client(http).get_list("/x", "items")
    assert [i["id"] for i in items] == [1, 2, 3]


@respx.mock
async def test_get_list_paginates_via_page_start_id_field():
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            Response(200, json={"items": [{"id": 1}], "pagination": {"page_start_id": 7}}),
            Response(200, json={"items": [{"id": 2}], "pagination": {}}),
        ],
    )
    async with httpx.AsyncClient() as http:
        items = await _client(http).get_list("/x", "items")
    assert [i["id"] for i in items] == [1, 2]
    assert "page_start_id=7" in str(route.calls.last.request.url)


@respx.mock
async def test_get_list_follows_zero_cursor():
    route = respx.get(f"{BASE}/x").mock(
        side_effect=[
            Response(200, json={"items": [{"id": 1}], "pagination": {"next_page_start_id": 0}}),
            Response(200, json={"items": [{"id": 2}], "pagination": {}}),
        ],
    )
    async with httpx.AsyncClient() as http:
        items = await _client(http).get_list("/x", "items")
    assert [i["id"] for i in items] == [1, 2]
    assert "page_start_id=0" in str(route.calls.last.request.url)


@respx.mock
async def test_exponential_backoff_is_capped():
    respx.get(f"{BASE}/x").mock(side_effect=[Response(503)] * 8 + [Response(200, json={"ok": 1})])
    spy = SleepSpy()
    async with httpx.AsyncClient() as http:
        await _client(http, sleep=spy, max_retries=8).request("GET", "/x")
    assert max(spy.calls) == 30.0


@respx.mock
async def test_long_error_body_is_truncated_in_message():
    respx.get(f"{BASE}/x").mock(return_value=Response(500, text="E" * 1000))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAPIError) as exc:
            await _client(http, sleep=SleepSpy(), max_retries=0).request("GET", "/x")
    assert len(str(exc.value)) < 400
