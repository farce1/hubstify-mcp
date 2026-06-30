import json

import respx
from fastmcp import Client
from httpx import Response

from app.main import mcp

BASE = "https://api.hubstaff.com/v2"


async def _call(tool: str, args: dict) -> str:
    async with Client(mcp) as client:
        result = await client.call_tool(tool, args)
    return result.content[0].text


def _mock_me():
    respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 7, "name": "Jo"}}))


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
async def test_log_time_localizes_naive_start_time_to_configured_zone(tool_context, monkeypatch):
    import app.config

    monkeypatch.setattr(app.config.settings, "default_timezone", "Europe/Warsaw")
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00"})
    body = json.loads(route.calls.last.request.content)
    assert body["start_time"] == "2026-06-30T09:00:00+02:00"  # CEST (DST) for Warsaw in summer


@respx.mock
async def test_log_time_passes_task_id(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00+00:00", "task_id": 11})
    body = json.loads(route.calls.last.request.content)
    assert body["task_id"] == 11


async def test_log_time_rejects_bad_start_time(tool_context):
    text = await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "yesterday"})
    assert text.startswith("Error:")


@respx.mock
async def test_log_time_includes_billable_false(tool_context):
    _mock_me()
    route = respx.post(f"{BASE}/users/7/time_entries").mock(return_value=Response(201, json={"success": True}))
    await _call("log_time", {"project_id": 1, "hours": 1, "start_time": "2026-06-30T09:00:00+00:00", "billable": False})
    body = json.loads(route.calls.last.request.content)
    assert body["billable"] is False


async def test_log_time_rejects_nonpositive_hours(tool_context):
    text = await _call("log_time", {"project_id": 1, "hours": 0})
    assert text.startswith("Error:")
    assert "hours" in text


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
