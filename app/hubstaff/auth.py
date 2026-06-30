import asyncio
import logging
import os
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import httpx
from pydantic import BaseModel

from app.hubstaff.errors import HubstaffAuthError

logger = logging.getLogger(__name__)

# Refresh this many seconds before the access token's stated expiry.
_EXPIRY_SKEW = 60
_DEFAULT_LIFETIME = 86400


class TokenSet(BaseModel):
    refresh_token: str
    access_token: str | None = None
    expires_at: float | None = None  # epoch seconds


class TokenManager:
    """Exchanges a Hubstaff PAT (refresh token) for access tokens.

    Caches the access token, persists the rotated refresh token to disk, and
    serialises refreshes so concurrent callers never trigger more than one
    exchange (Hubstaff allows only 5 refreshes/hour/token). Exactly one manager
    should own a given token store.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        refresh_token: str,
        token_url: str,
        token_store: Path,
        now: Callable[[], float] = time.time,
    ):
        self._http = http
        self._token_url = token_url
        self._token_store = Path(token_store).expanduser()
        self._now = now
        self._lock = asyncio.Lock()
        self._token = self._load() or TokenSet(refresh_token=refresh_token)

    async def get_access_token(self) -> str:
        token = self._token.access_token
        if token is not None and not self._is_expired():
            return token
        async with self._lock:
            token = self._token.access_token
            if token is not None and not self._is_expired():
                return token
            return await self._exchange()

    async def force_refresh(self, stale: str) -> str:
        async with self._lock:
            current = self._token.access_token
            if current is not None and current != stale:
                return current
            return await self._exchange()

    async def _exchange(self) -> str:
        if not self._token.refresh_token:
            raise HubstaffAuthError(
                "HUBSTAFF_PERSONAL_ACCESS_TOKEN is not set. Create a Personal Access Token at "
                "https://developer.hubstaff.com/account/personal-access-tokens",
            )
        try:
            response = await self._http.post(
                self._token_url,
                data={"grant_type": "refresh_token", "refresh_token": self._token.refresh_token},
            )
        except httpx.HTTPError as exc:
            raise HubstaffAuthError(f"Hubstaff token refresh request failed: {exc}") from exc

        if response.status_code != httpx.codes.OK:
            raise HubstaffAuthError(self._describe_failure(response))

        body = self._parse_body(response)
        access_token = body.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HubstaffAuthError("Hubstaff token response did not include an access_token")

        self._token = TokenSet(
            refresh_token=body.get("refresh_token") or self._token.refresh_token,
            access_token=access_token,
            expires_at=self._now() + body.get("expires_in", _DEFAULT_LIFETIME),
        )
        self._persist()
        return access_token

    def _is_expired(self) -> bool:
        if self._token.expires_at is None:
            return True
        return self._now() >= self._token.expires_at - _EXPIRY_SKEW

    def _load(self) -> TokenSet | None:
        try:
            raw = self._token_store.read_text()
        except OSError:
            return None
        try:
            return TokenSet.model_validate_json(raw)
        except ValueError:
            logger.warning("Ignoring corrupt token store at %s; using the configured refresh token", self._token_store)
            return None

    def _persist(self) -> None:
        self._token_store.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Write to a 0600 temp file in the same dir, then atomically rename so the
        # rotated refresh token is never lost to a partial write or left readable.
        fd, tmp_name = tempfile.mkstemp(dir=self._token_store.parent, prefix=".tokens-", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(self._token.model_dump_json(indent=2))
            os.replace(tmp, self._token_store)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    @staticmethod
    def _parse_body(response: httpx.Response) -> dict:
        try:
            data = response.json()
        except ValueError as exc:
            raise HubstaffAuthError("Hubstaff token response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise HubstaffAuthError("Hubstaff token response had an unexpected shape")
        return data

    @staticmethod
    def _describe_failure(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        reason = payload.get("error_description") or payload.get("error") or response.text
        return f"Hubstaff token refresh failed ({response.status_code}): {reason}"
