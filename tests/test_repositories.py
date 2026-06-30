import json
from datetime import date, datetime, timezone
from urllib.parse import unquote

import pytest
import respx
from httpx import Response

from app.domain.time_entry import NewTimeEntry
from app.domain.value_objects import DateRange
from app.hubstaff.errors import HubstaffAPIError
from app.repositories.activity_repository import ActivityRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.time_entry_repository import TimeEntryRepository
from app.repositories.user_repository import UserRepository

BASE = "https://api.hubstaff.com/v2"


@respx.mock
async def test_user_repository_get_current_user(api):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 5, "name": "Jo"}}))
    user = await UserRepository(api).get_current_user()
    assert (user.id, user.name) == (5, "Jo")


@respx.mock
async def test_user_repository_raises_on_missing_envelope(api):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"unexpected": 1}))
    with pytest.raises(HubstaffAPIError):
        await UserRepository(api).get_current_user()


@respx.mock
async def test_organization_repository_list(api):
    respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [{"id": 1, "name": "Acme"}], "pagination": {}}),
    )
    orgs = await OrganizationRepository(api).list_organizations()
    assert [o.name for o in orgs] == ["Acme"]


@respx.mock
async def test_repository_aggregates_paginated_results(api):
    respx.get(f"{BASE}/organizations").mock(
        side_effect=[
            Response(200, json={"organizations": [{"id": 1, "name": "Acme"}], "pagination": {"next_page_start_id": 2}}),
            Response(200, json={"organizations": [{"id": 2, "name": "Beta"}], "pagination": {}}),
        ],
    )
    orgs = await OrganizationRepository(api).list_organizations()
    assert [o.name for o in orgs] == ["Acme", "Beta"]


@respx.mock
async def test_project_repository_list_with_status(api):
    route = respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(200, json={"projects": [{"id": 2, "name": "Web"}], "pagination": {}}),
    )
    projects = await ProjectRepository(api).list_projects(9, status="active")
    assert projects[0].id == 2
    assert "status=active" in str(route.calls.last.request.url)


@respx.mock
async def test_project_list_omits_status_when_none(api):
    route = respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(200, json={"projects": [], "pagination": {}}),
    )
    await ProjectRepository(api).list_projects(9)
    assert "status=" not in str(route.calls.last.request.url)


@respx.mock
async def test_task_repository_list(api):
    respx.get(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(200, json={"tasks": [{"id": 7, "summary": "Do it"}], "pagination": {}}),
    )
    tasks = await TaskRepository(api).list_tasks(3)
    assert tasks[0].summary == "Do it"


@respx.mock
async def test_task_repository_create_sends_fields(api):
    route = respx.post(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(201, json={"task": {"id": 8, "summary": "New"}})
    )
    task = await TaskRepository(api).create(3, summary="New", details="d")
    assert task.id == 8
    body = json.loads(route.calls.last.request.content)
    assert body == {"summary": "New", "details": "d"}


@respx.mock
async def test_task_create_with_assignee_ids(api):
    route = respx.post(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(201, json={"task": {"id": 8, "summary": "S"}})
    )
    await TaskRepository(api).create(3, summary="S", assignee_ids=[1, 2])
    body = json.loads(route.calls.last.request.content)
    assert body == {"summary": "S", "assignee_ids": [1, 2]}


@respx.mock
async def test_task_create_tolerates_flat_response(api):
    respx.post(f"{BASE}/projects/3/tasks").mock(return_value=Response(201, json={"id": 9, "summary": "Flat"}))
    task = await TaskRepository(api).create(3, summary="Flat")
    assert task.id == 9


@respx.mock
async def test_member_repository_list_includes_users(api):
    route = respx.get(f"{BASE}/organizations/9/members").mock(
        return_value=Response(
            200, json={"members": [{"user_id": 5, "user": {"id": 5, "name": "Jo"}}], "pagination": {}}
        ),
    )
    members = await MemberRepository(api).list_members(9)
    assert members[0].user is not None
    assert members[0].user.name == "Jo"
    assert "include=users" in str(route.calls.last.request.url)


@respx.mock
async def test_member_without_nested_user(api):
    respx.get(f"{BASE}/organizations/9/members").mock(
        return_value=Response(200, json={"members": [{"user_id": 5}], "pagination": {}}),
    )
    members = await MemberRepository(api).list_members(9)
    assert members[0].user is None


@respx.mock
async def test_team_repository_list(api):
    respx.get(f"{BASE}/organizations/9/teams").mock(
        return_value=Response(200, json={"teams": [{"id": 1, "name": "Core"}], "pagination": {}}),
    )
    teams = await TeamRepository(api).list_teams(9)
    assert teams[0].name == "Core"


@respx.mock
async def test_activity_repository_daily(api):
    route = respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [{"id": 1, "date": "2026-06-30", "user_id": 5, "project_id": 3, "tracked": 3600}],
                "pagination": {},
            },
        ),
    )
    date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 30))
    rows = await ActivityRepository(api).daily(9, date_range, user_ids=[5])
    assert rows[0].tracked == 3600
    url = unquote(str(route.calls.last.request.url))
    assert "date[start]=2026-06-01" in url
    assert "date[stop]=2026-06-30" in url
    assert "user_ids=5" in url


@respx.mock
async def test_time_entry_repository_create(api):
    route = respx.post(f"{BASE}/users/5/time_entries").mock(return_value=Response(201, json={"success": True}))
    entry = NewTimeEntry(
        project_id=3,
        start_time=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        tracked=7200,
        note="x",
    )
    result = await TimeEntryRepository(api).create(5, entry)
    assert result == {"success": True}
    body = json.loads(route.calls.last.request.content)
    assert body == {"project_id": 3, "start_time": "2026-06-30T09:00:00+00:00", "tracked": 7200, "note": "x"}
