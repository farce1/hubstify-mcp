import json

import pytest
import respx
from fastmcp.exceptions import ToolError
from httpx import Response

from tests.conftest import BASE
from tests.conftest import call_tool as _call
from tests.conftest import mock_me as _mock_me


@respx.mock
async def test_log_time_creates_entry(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    text = await _call(
        "log_time",
        {"project_id": 1, "hours": 2, "start_time": "2026-06-30T09:00:00+00:00", "note": "API integration"},
    )
    assert "Logged" in text
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "project_id": 1,
        "start_time": "2026-06-30T09:00:00+00:00",
        "tracked": 7200,
        "note": "API integration",
    }


@respx.mock
async def test_log_time_converts_decimal_hours_and_defaults_start(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1.5})
    body = json.loads(route.calls.last.request.content)
    assert body["tracked"] == 5400
    assert "start_time" in body


@respx.mock
async def test_log_time_localizes_naive_start_time_to_user_timezone(tool_context):
    _mock_me(time_zone="Europe/Berlin")
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00"})
    body = json.loads(route.calls.last.request.content)
    assert body["start_time"] == "2026-06-30T09:00:00+02:00"  # CEST (DST) for Berlin in summer


@respx.mock
async def test_log_time_falls_back_to_utc_when_account_has_no_timezone(tool_context):
    _mock_me()  # no time_zone on the account
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00"})
    body = json.loads(route.calls.last.request.content)
    assert body["start_time"] == "2026-06-30T09:00:00+00:00"  # UTC fallback


@respx.mock
async def test_log_time_passes_task_id(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00+00:00", "task_id": 11})
    body = json.loads(route.calls.last.request.content)
    assert body["task_id"] == 11


async def test_log_time_rejects_bad_start_time(tool_context):
    with pytest.raises(ToolError):
        await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "yesterday"})


@respx.mock
async def test_log_time_includes_billable_false(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00+00:00", "billable": False})
    body = json.loads(route.calls.last.request.content)
    assert body["billable"] is False


async def test_log_time_rejects_nonpositive_hours(tool_context):
    with pytest.raises(ToolError, match="hours"):
        await _call("log_time", {"project_id": 1, "hours": 0})


@respx.mock
async def test_create_task(tool_context):
    route = respx.post(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(201, json={"task": {"id": 8, "summary": "Write docs"}})
    )
    text = await _call("create_task", {"project_id": 3, "summary": "Write docs"})
    assert "Write docs" in text
    assert "8" in text
    body = json.loads(route.calls.last.request.content)
    assert body["summary"] == "Write docs"
