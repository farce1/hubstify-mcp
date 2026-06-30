import httpx

from app.config import settings
from app.hubstaff.auth import TokenManager
from app.hubstaff.client import HubstaffClient
from app.hubstaff.errors import HubstaffError
from app.repositories.activity_repository import ActivityRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.time_entry_repository import TimeEntryRepository
from app.repositories.user_repository import UserRepository
from app.services.timesheet_service import TimesheetService


class Context:
    """Wires the repositories and services over a single Hubstaff client."""

    def __init__(self, client: HubstaffClient):
        self.client = client
        self.users = UserRepository(client)
        self.organizations = OrganizationRepository(client)
        self.projects = ProjectRepository(client)
        self.tasks = TaskRepository(client)
        self.members = MemberRepository(client)
        self.teams = TeamRepository(client)
        self.activities = ActivityRepository(client)
        self.time_entries = TimeEntryRepository(client)
        self.timesheets = TimesheetService(self.activities)
        self._current_user_id: int | None = None
        self._default_organization_id: int | None = None
        self._project_names: dict[int, dict[int, str]] = {}

    async def current_user_id(self) -> int:
        if self._current_user_id is None:
            self._current_user_id = (await self.users.get_current_user()).id
        return self._current_user_id

    async def default_organization_id(self) -> int:
        if self._default_organization_id is None:
            if settings.hubstaff_default_organization_id is not None:
                self._default_organization_id = settings.hubstaff_default_organization_id
            else:
                organizations = await self.organizations.list_organizations()
                if not organizations:
                    raise HubstaffError("No Hubstaff organizations are available for this account.")
                self._default_organization_id = organizations[0].id
        return self._default_organization_id

    async def project_names(self, organization_id: int) -> dict[int, str]:
        if organization_id not in self._project_names:
            projects = await self.projects.list_projects(organization_id, status="all")
            self._project_names[organization_id] = {project.id: project.name for project in projects}
        return self._project_names[organization_id]


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
