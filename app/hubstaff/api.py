from typing import Any

from app.domain.activity import DailyActivity
from app.domain.member import OrganizationMember
from app.domain.organization import Organization
from app.domain.project import Project
from app.domain.task import Task
from app.domain.team import Team
from app.domain.time_entry import NewTimeEntry
from app.domain.user import User
from app.domain.value_objects import DateRange
from app.hubstaff.client import HubstaffClient
from app.hubstaff.errors import HubstaffAPIError


async def get_current_user(client: HubstaffClient) -> User:
    data = await client.request("GET", "/users/me")
    if not isinstance(data, dict) or "user" not in data:
        raise HubstaffAPIError("Unexpected Hubstaff response for /users/me", body=data)
    return User.model_validate(data["user"])


async def list_organizations(client: HubstaffClient) -> list[Organization]:
    items = await client.get_list("/organizations", "organizations")
    return [Organization.model_validate(item) for item in items]


async def list_projects(client: HubstaffClient, organization_id: int, status: str | None = None) -> list[Project]:
    # Omitting status returns Hubstaff's default (active projects only).
    items = await client.get_list(
        f"/organizations/{organization_id}/projects",
        "projects",
        params={"status": status},
    )
    return [Project.model_validate(item) for item in items]


async def list_members(client: HubstaffClient, organization_id: int) -> list[OrganizationMember]:
    items = await client.get_list(
        f"/organizations/{organization_id}/members",
        "members",
        params={"include": "users"},
    )
    return [OrganizationMember.model_validate(item) for item in items]


async def list_teams(client: HubstaffClient, organization_id: int) -> list[Team]:
    items = await client.get_list(f"/organizations/{organization_id}/teams", "teams")
    return [Team.model_validate(item) for item in items]


async def list_tasks(client: HubstaffClient, project_id: int, status: str | None = None) -> list[Task]:
    items = await client.get_list(f"/projects/{project_id}/tasks", "tasks", params={"status": status})
    return [Task.model_validate(item) for item in items]


async def create_task(
    client: HubstaffClient,
    project_id: int,
    summary: str,
    details: str | None = None,
    assignee_ids: list[int] | None = None,
) -> Task:
    body: dict[str, object] = {"summary": summary}
    if details is not None:
        body["details"] = details
    if assignee_ids is not None:
        body["assignee_ids"] = assignee_ids
    data = await client.request("POST", f"/projects/{project_id}/tasks", json=body)
    # Create response envelope is not firmly documented; tolerate flat or {"task": ...}.
    payload = data.get("task", data) if isinstance(data, dict) else data
    return Task.model_validate(payload)


async def daily_activities(
    client: HubstaffClient,
    organization_id: int,
    date_range: DateRange,
    user_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
) -> list[DailyActivity]:
    params = {
        "date[start]": date_range.start.isoformat(),
        "date[stop]": date_range.stop.isoformat(),
        "user_ids": user_ids,
        "project_ids": project_ids,
    }
    items = await client.get_list(
        f"/organizations/{organization_id}/activities/daily",
        "daily_activities",
        params=params,
    )
    return [DailyActivity.model_validate(item) for item in items]


async def create_time_entry(client: HubstaffClient, user_id: int, entry: NewTimeEntry) -> Any:
    return await client.request(
        "POST",
        f"/users/{user_id}/time_entries",
        json=entry.model_dump(mode="json", exclude_none=True),
    )
