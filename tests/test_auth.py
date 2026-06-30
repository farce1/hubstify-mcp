import asyncio
import json

import httpx
import pytest
import respx
from httpx import Response

from app.hubstaff.auth import TokenManager
from app.hubstaff.errors import HubstaffAuthError

TOKEN_URL = "https://account.hubstaff.com/access_tokens"


class Clock:
    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def _token_response(access: str, refresh: str, expires_in: int = 86400) -> Response:
    return Response(
        200,
        json={"token_type": "bearer", "access_token": access, "refresh_token": refresh, "expires_in": expires_in},
    )


def _manager(http: httpx.AsyncClient, tmp_path, clock=None, refresh_token="pat-0"):
    return TokenManager(
        http=http,
        refresh_token=refresh_token,
        token_url=TOKEN_URL,
        token_store=tmp_path / "tokens.json",
        now=clock or Clock(),
    )


@respx.mock
async def test_exchanges_refresh_token_for_access_token(tmp_path):
    route = respx.post(TOKEN_URL).mock(return_value=_token_response("access-1", "pat-1"))
    async with httpx.AsyncClient() as http:
        token = await _manager(http, tmp_path).get_access_token()
    assert token == "access-1"
    body = route.calls.last.request.content.decode()
    assert "grant_type=refresh_token" in body
    assert "pat-0" in body


@respx.mock
async def test_persists_rotated_refresh_token(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=_token_response("access-1", "rotated-pat"))
    store = tmp_path / "tokens.json"
    async with httpx.AsyncClient() as http:
        await _manager(http, tmp_path).get_access_token()
    saved = json.loads(store.read_text())
    assert saved["refresh_token"] == "rotated-pat"
    assert saved["access_token"] == "access-1"


@respx.mock
async def test_caches_access_token_within_validity(tmp_path):
    route = respx.post(TOKEN_URL).mock(return_value=_token_response("access-1", "pat-1"))
    async with httpx.AsyncClient() as http:
        manager = _manager(http, tmp_path)
        await manager.get_access_token()
        await manager.get_access_token()
    assert route.call_count == 1


@respx.mock
async def test_refreshes_after_expiry_using_rotated_token(tmp_path):
    route = respx.post(TOKEN_URL).mock(
        side_effect=[_token_response("access-1", "pat-1", expires_in=3600), _token_response("access-2", "pat-2")],
    )
    clock = Clock()
    async with httpx.AsyncClient() as http:
        manager = _manager(http, tmp_path, clock=clock)
        assert await manager.get_access_token() == "access-1"
        clock.advance(3600)
        assert await manager.get_access_token() == "access-2"
    assert route.call_count == 2
    assert "pat-1" in route.calls.last.request.content.decode()


@respx.mock
async def test_loads_persisted_token_and_prefers_it_over_env(tmp_path):
    store = tmp_path / "tokens.json"
    store.write_text(
        json.dumps({"refresh_token": "persisted-pat", "access_token": "persisted-access", "expires_at": 99999}),
    )
    route = respx.post(TOKEN_URL)
    async with httpx.AsyncClient() as http:
        manager = _manager(http, tmp_path, clock=Clock(1000.0), refresh_token="env-pat")
        token = await manager.get_access_token()
    assert token == "persisted-access"
    assert not route.called


@respx.mock
async def test_force_refresh_is_single_flight_for_same_stale_token(tmp_path):
    route = respx.post(TOKEN_URL).mock(
        side_effect=[_token_response("access-1", "pat-1"), _token_response("access-2", "pat-2")],
    )
    async with httpx.AsyncClient() as http:
        manager = _manager(http, tmp_path)
        first = await manager.get_access_token()
        new1, new2 = await asyncio.gather(manager.force_refresh(first), manager.force_refresh(first))
    assert new1 == new2 == "access-2"
    assert route.call_count == 2  # one initial exchange + exactly one forced refresh


@respx.mock
async def test_failed_refresh_raises_auth_error_with_reason(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=Response(400, json={"error": "rate_limit"}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAuthError, match="rate_limit"):
            await _manager(http, tmp_path).get_access_token()


@respx.mock
async def test_concurrent_get_access_token_is_single_flight(tmp_path):
    route = respx.post(TOKEN_URL).mock(return_value=_token_response("access-1", "pat-1"))
    async with httpx.AsyncClient() as http:
        manager = _manager(http, tmp_path)
        tokens = await asyncio.gather(manager.get_access_token(), manager.get_access_token())
    assert tokens == ["access-1", "access-1"]
    assert route.call_count == 1


@respx.mock
async def test_token_store_is_created_private(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=_token_response("access-1", "pat-1"))
    store = tmp_path / "tokens.json"
    async with httpx.AsyncClient() as http:
        await _manager(http, tmp_path).get_access_token()
    assert (store.stat().st_mode & 0o777) == 0o600


@respx.mock
async def test_refresh_token_not_leaked_in_error(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=Response(400, json={"error": "bad"}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAuthError) as exc:
            await _manager(http, tmp_path, refresh_token="super-secret-pat").get_access_token()
    assert "super-secret-pat" not in str(exc.value)


@respx.mock
async def test_success_body_without_access_token_raises_auth_error(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=Response(200, json={"token_type": "bearer"}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAuthError):
            await _manager(http, tmp_path).get_access_token()


@respx.mock
async def test_missing_refresh_token_raises_clear_error(tmp_path):
    route = respx.post(TOKEN_URL)
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAuthError, match="token"):
            await _manager(http, tmp_path, refresh_token="").get_access_token()
    assert not route.called


@respx.mock
async def test_non_dict_error_body_raises_auth_error(tmp_path):
    respx.post(TOKEN_URL).mock(return_value=Response(400, json="rate_limit"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(HubstaffAuthError, match="rate_limit"):
            await _manager(http, tmp_path).get_access_token()
