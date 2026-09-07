import json
from datetime import date, datetime, timezone
from urllib.parse import unquote

import pytest
import respx
from httpx import Response

from app.domain.models import DateRange
from app.domain.time_entry import NewTimeEntry
from app.hubstaff.api import (
    create_task,
    create_time_entry,
    daily_activities,
    get_current_user,
    list_members,
    list_organizations,
    list_projects,
    list_tasks,
    list_teams,
)
from app.hubstaff.errors import HubstaffAPIError

BASE = "https://api.hubstaff.com/v2"


@respx.mock
async def test_get_current_user(api):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 5, "name": "Jo"}}))
    user = await get_current_user(api)
    assert (user.id, user.name) == (5, "Jo")


@respx.mock
async def test_get_current_user_raises_on_missing_envelope(api):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"unexpected": 1}))
    with pytest.raises(HubstaffAPIError):
        await get_current_user(api)


@respx.mock
async def test_list_organizations(api):
    respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [{"id": 1, "name": "Acme"}], "pagination": {}}),
    )
    orgs = await list_organizations(api)
    assert [o.name for o in orgs] == ["Acme"]


@respx.mock
async def test_list_projects_with_status(api):
    route = respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(200, json={"projects": [{"id": 2, "name": "Web"}], "pagination": {}}),
    )
    projects = await list_projects(api, 9, status="active")
    assert projects[0].id == 2
    assert "status=active" in str(route.calls.last.request.url)


@respx.mock
async def test_list_projects_omits_status_when_none(api):
    route = respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(200, json={"projects": [], "pagination": {}}),
    )
    await list_projects(api, 9)
    assert "status=" not in str(route.calls.last.request.url)


@respx.mock
async def test_list_tasks(api):
    respx.get(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(200, json={"tasks": [{"id": 7, "summary": "Do it"}], "pagination": {}}),
    )
    tasks = await list_tasks(api, 3)
    assert tasks[0].summary == "Do it"


@respx.mock
async def test_create_task_sends_fields(api):
    route = respx.post(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(201, json={"task": {"id": 8, "summary": "New"}})
    )
    task = await create_task(api, 3, summary="New", details="d")
    assert task.id == 8
    body = json.loads(route.calls.last.request.content)
    assert body == {"summary": "New", "details": "d"}


@respx.mock
async def test_create_task_with_assignee_ids(api):
    route = respx.post(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(201, json={"task": {"id": 8, "summary": "S"}})
    )
    await create_task(api, 3, summary="S", assignee_ids=[1, 2])
    body = json.loads(route.calls.last.request.content)
    assert body == {"summary": "S", "assignee_ids": [1, 2]}


@respx.mock
async def test_create_task_tolerates_flat_response(api):
    respx.post(f"{BASE}/projects/3/tasks").mock(return_value=Response(201, json={"id": 9, "summary": "Flat"}))
    task = await create_task(api, 3, summary="Flat")
    assert task.id == 9


@respx.mock
async def test_list_members_includes_users(api):
    route = respx.get(f"{BASE}/organizations/9/members").mock(
        return_value=Response(
            200, json={"members": [{"user_id": 5, "user": {"id": 5, "name": "Jo"}}], "pagination": {}}
        ),
    )
    members = await list_members(api, 9)
    assert members[0].user is not None
    assert members[0].user.name == "Jo"
    assert "include=users" in str(route.calls.last.request.url)


@respx.mock
async def test_member_without_nested_user(api):
    respx.get(f"{BASE}/organizations/9/members").mock(
        return_value=Response(200, json={"members": [{"user_id": 5}], "pagination": {}}),
    )
    members = await list_members(api, 9)
    assert members[0].user is None


@respx.mock
async def test_list_teams(api):
    respx.get(f"{BASE}/organizations/9/teams").mock(
        return_value=Response(200, json={"teams": [{"id": 1, "name": "Core"}], "pagination": {}}),
    )
    teams = await list_teams(api, 9)
    assert teams[0].name == "Core"


@respx.mock
async def test_daily_activities(api):
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
    rows = await daily_activities(api, 9, date_range, user_ids=[5])
    assert rows[0].tracked == 3600
    url = unquote(str(route.calls.last.request.url))
    assert "date[start]=2026-06-01" in url
    assert "date[stop]=2026-06-30" in url
    assert "user_ids=5" in url


@respx.mock
async def test_create_time_entry_omits_unset_optionals(api):
    route = respx.post(f"{BASE}/users/5/time_entries").mock(return_value=Response(201, json={"success": True}))
    entry = NewTimeEntry(
        project_id=3,
        start_time=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        tracked=7200,
        note="x",
    )
    result = await create_time_entry(api, 5, entry)
    assert result == {"success": True}
    body = json.loads(route.calls.last.request.content)
    assert body == {"project_id": 3, "start_time": "2026-06-30T09:00:00+00:00", "tracked": 7200, "note": "x"}
