from urllib.parse import unquote

import respx
from httpx import Response

from tests._helpers import BASE, mock_me, mock_projects
from tests._helpers import call_tool as _call


def _mock_identity_and_projects():
    mock_me()
    mock_projects()


@respx.mock
async def test_get_timesheet_summarises_per_project(tool_context):
    _mock_identity_and_projects()
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [
                    {"id": 1, "date": "2026-06-01", "user_id": 7, "project_id": 1, "tracked": 3600},
                    {"id": 2, "date": "2026-06-02", "user_id": 7, "project_id": 1, "tracked": 1800},
                ],
                "pagination": {},
            },
        ),
    )
    text = await _call("get_timesheet", {"organization_id": 9, "period": "this_week"})
    assert "Acme" in text
    assert "1h 30m" in text


@respx.mock
async def test_get_time_entries_lists_per_day(tool_context):
    _mock_identity_and_projects()
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [{"id": 1, "date": "2026-06-01", "user_id": 7, "project_id": 1, "tracked": 3600}],
                "pagination": {},
            },
        ),
    )
    text = await _call("get_time_entries", {"organization_id": 9, "period": "this_week"})
    assert "Acme" in text
    assert "1h" in text
    assert "2026-06-01" in text


@respx.mock
async def test_get_time_entries_filters_by_project(tool_context):
    _mock_identity_and_projects()
    daily = respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(200, json={"daily_activities": [], "pagination": {}}),
    )
    await _call("get_time_entries", {"organization_id": 9, "period": "this_week", "project_id": 1})
    assert "project_ids=1" in unquote(str(daily.calls.last.request.url))


@respx.mock
async def test_get_timesheet_scopes_to_current_user(tool_context):
    _mock_identity_and_projects()
    daily = respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(200, json={"daily_activities": [], "pagination": {}}),
    )
    await _call("get_timesheet", {"organization_id": 9, "period": "this_week"})
    assert "user_ids=7" in unquote(str(daily.calls.last.request.url))


@respx.mock
async def test_get_time_entries_scopes_to_current_user(tool_context):
    _mock_identity_and_projects()
    daily = respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(200, json={"daily_activities": [], "pagination": {}}),
    )
    await _call("get_time_entries", {"organization_id": 9, "period": "this_week"})
    assert "user_ids=7" in unquote(str(daily.calls.last.request.url))


@respx.mock
async def test_get_time_entries_falls_back_to_project_id_when_name_unknown(tool_context):
    _mock_identity_and_projects()  # names map only has project 1
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [{"id": 1, "date": "2026-06-01", "user_id": 7, "project_id": 2, "tracked": 600}],
                "pagination": {},
            },
        ),
    )
    text = await _call("get_time_entries", {"organization_id": 9, "period": "this_week"})
    assert "project 2" in text


@respx.mock
async def test_get_timesheet_sorts_projects_by_duration(tool_context):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 7, "name": "Jo"}}))
    respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(
            200,
            json={"projects": [{"id": 1, "name": "Acme"}, {"id": 2, "name": "Beta"}], "pagination": {}},
        ),
    )
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [
                    {"id": 1, "date": "2026-06-01", "user_id": 7, "project_id": 1, "tracked": 600},
                    {"id": 2, "date": "2026-06-01", "user_id": 7, "project_id": 2, "tracked": 3600},
                ],
                "pagination": {},
            },
        ),
    )
    text = await _call("get_timesheet", {"organization_id": 9, "period": "this_week"})
    assert text.index("Beta") < text.index("Acme")


@respx.mock
async def test_get_timesheet_invalid_period_is_user_error(tool_context):
    text = await _call("get_timesheet", {"organization_id": 9, "period": "fortnight"})
    assert text.startswith("Error:")
    assert "fortnight" in text


@respx.mock
async def test_get_timesheet_empty(tool_context):
    _mock_identity_and_projects()
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(200, json={"daily_activities": [], "pagination": {}}),
    )
    text = await _call("get_timesheet", {"organization_id": 9, "period": "today"})
    assert "No tracked time" in text
