import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx

from app.hubstaff.errors import HubstaffAPIError, HubstaffRateLimitError

_BACKOFF_BASE = 0.5
_BACKOFF_CAP = 30.0
_PAGE_LIMIT = 500
_MAX_REASON = 200


class TokenProvider(Protocol):
    async def get_access_token(self) -> str: ...
    async def force_refresh(self, stale: str) -> str: ...


class HubstaffClient:
    """Authenticated transport for the Hubstaff v2 API.

    Adds Bearer auth, a single reactive token refresh on 401, retry with
    backoff on 429/5xx, and cursor pagination over list endpoints.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        tokens: TokenProvider,
        base_url: str,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        max_retries: int = 3,
    ):
        self._http = http
        self._tokens = tokens
        self._base_url = base_url.rstrip("/")
        self._sleep = sleep
        self._max_retries = max_retries

    async def request(self, method: str, path: str, *, params: dict | None = None, json: Any = None) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        query = _clean_params(params)
        refreshed = False
        attempt = 0
        while True:
            token = await self._tokens.get_access_token()
            response = await self._http.request(
                method,
                url,
                params=query,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == httpx.codes.UNAUTHORIZED and not refreshed:
                await self._tokens.force_refresh(token)
                refreshed = True
                continue
            if _is_retryable(response) and attempt < self._max_retries:
                await self._sleep(self._retry_delay(response, attempt))
                attempt += 1
                continue
            if response.is_success:
                return _parse(response)
            raise _error(response)

    async def get_list(self, path: str, key: str, *, params: dict | None = None) -> list[dict]:
        items: list[dict] = []
        page_params = dict(params or {})
        page_params.setdefault("page_limit", _PAGE_LIMIT)
        seen: set = set()
        while True:
            page = await self.request("GET", path, params=page_params)
            if not isinstance(page, dict):
                return items
            items.extend(page.get(key, []))
            cursor = _next_cursor(page)
            if cursor is None or cursor in seen:
                return items
            seen.add(cursor)
            page_params["page_start_id"] = cursor

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                return float(retry_after)
        return min(_BACKOFF_BASE * (2**attempt), _BACKOFF_CAP)


def _is_retryable(response: httpx.Response) -> bool:
    return (
        response.status_code == httpx.codes.TOO_MANY_REQUESTS
        or response.status_code >= httpx.codes.INTERNAL_SERVER_ERROR
    )


def _clean_params(params: dict | None) -> dict | None:
    if not params:
        return None
    return {key: value for key, value in params.items() if value is not None}


def _parse(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def _next_cursor(page: dict) -> Any:
    pagination = page.get("pagination")
    if not isinstance(pagination, dict):
        return None
    nxt = pagination.get("next_page_start_id")
    return nxt if nxt is not None else pagination.get("page_start_id")


def _error(response: httpx.Response) -> HubstaffAPIError:
    body = _parse(response)
    reason = None
    if isinstance(body, dict):
        reason = body.get("error_description") or body.get("error")
    elif isinstance(body, str):
        reason = body
    detail = (reason or response.reason_phrase)[:_MAX_REASON]
    where = f"{response.request.method} {response.request.url.path}"
    message = f"Hubstaff API {response.status_code} on {where}: {detail}"
    if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        return HubstaffRateLimitError(message, status=response.status_code, body=body)
    return HubstaffAPIError(message, status=response.status_code, body=body)
