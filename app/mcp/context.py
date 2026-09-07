from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.config import settings
from app.domain.models import User
from app.hubstaff import api
from app.hubstaff.auth import TokenManager
from app.hubstaff.client import HubstaffClient
from app.hubstaff.errors import HubstaffError


class Context:
    """Per-process cache of the lookups every tool repeats, over a single client."""

    def __init__(self, client: HubstaffClient):
        self.client = client
        self._current_user: User | None = None
        self._current_timezone: ZoneInfo | None = None
        self._default_organization_id: int | None = None
        self._project_names: dict[int, dict[int, str]] = {}

    async def current_user(self) -> User:
        if self._current_user is None:
            self._current_user = await api.get_current_user(self.client)
        return self._current_user

    async def current_timezone(self) -> ZoneInfo:
        # Prefer the timezone on the Hubstaff account so logged times match what the
        # user sees; fall back to UTC only when it's absent/invalid.
        if self._current_timezone is None:
            self._current_timezone = _resolve_zone((await self.current_user()).time_zone)
        return self._current_timezone

    async def default_organization_id(self) -> int:
        if self._default_organization_id is None:
            if settings.hubstaff_default_organization_id is not None:
                self._default_organization_id = settings.hubstaff_default_organization_id
            else:
                organizations = await api.list_organizations(self.client)
                if not organizations:
                    raise HubstaffError("No Hubstaff organizations are available for this account.")
                self._default_organization_id = organizations[0].id
        return self._default_organization_id

    async def project_names(self, organization_id: int) -> dict[int, str]:
        if organization_id not in self._project_names:
            projects = await api.list_projects(self.client, organization_id, status="all")
            self._project_names[organization_id] = {project.id: project.name for project in projects}
        return self._project_names[organization_id]


def _resolve_zone(name: str | None) -> ZoneInfo:
    # The Hubstaff account timezone is the source of truth; UTC is only a last resort
    # for the rare account that has none set (or an unrecognized name).
    if name:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return ZoneInfo("UTC")


def build_context() -> Context:
    # The client is owned for the lifetime of the stdio process; the OS reclaims
    # its sockets at exit, so there is no explicit shutdown.
    http = httpx.AsyncClient(timeout=30)
    tokens = TokenManager(
        http=http,
        refresh_token=settings.hubstaff_personal_access_token,
        token_url=settings.hubstaff_token_url,
        token_store=settings.hubstaff_token_store,
    )
    client = HubstaffClient(http=http, tokens=tokens, base_url=settings.hubstaff_api_base)
    return Context(client)


_context: Context | None = None


def get_context() -> Context:
    global _context
    if _context is None:
        _context = build_context()
    return _context
