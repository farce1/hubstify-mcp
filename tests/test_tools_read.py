import respx
from httpx import Response

from tests._helpers import BASE
from tests._helpers import call_tool as _call


@respx.mock
async def test_get_current_user(tool_context):
    respx.get(f"{BASE}/users/me").mock(
        return_value=Response(200, json={"user": {"id": 5, "name": "Jo", "email": "jo@x.com"}}),
    )
    text = await _call("get_current_user", {})
    assert "Jo" in text
    assert "5" in text


@respx.mock
async def test_get_organizations(tool_context):
    respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [{"id": 1, "name": "Acme"}], "pagination": {}}),
    )
    text = await _call("get_organizations", {})
    assert "Acme" in text


@respx.mock
async def test_get_projects_defaults_to_primary_org(tool_context):
    respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [{"id": 9, "name": "Acme"}], "pagination": {}}),
    )
    respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(
            200, json={"projects": [{"id": 2, "name": "Web", "status": "active", "billable": True}], "pagination": {}}
        ),
    )
    text = await _call("get_projects", {})
    assert "Web" in text
    assert "billable" in text


@respx.mock
async def test_get_projects_with_explicit_org(tool_context):
    route = respx.get(f"{BASE}/organizations/7/projects").mock(
        return_value=Response(200, json={"projects": [{"id": 1, "name": "Solo"}], "pagination": {}}),
    )
    text = await _call("get_projects", {"organization_id": 7})
    assert "Solo" in text
    assert route.called


@respx.mock
async def test_default_org_override_skips_org_lookup(tool_context, monkeypatch):
    import app.config

    monkeypatch.setattr(app.config.settings, "hubstaff_default_organization_id", 42)
    projects = respx.get(f"{BASE}/organizations/42/projects").mock(
        return_value=Response(200, json={"projects": [], "pagination": {}}),
    )
    orgs = respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [], "pagination": {}}),
    )
    await _call("get_projects", {})
    assert projects.called
    assert not orgs.called


@respx.mock
async def test_default_org_is_resolved_once_and_cached(tool_context):
    org_route = respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [{"id": 9, "name": "Acme"}], "pagination": {}}),
    )
    respx.get(f"{BASE}/organizations/9/projects").mock(
        return_value=Response(200, json={"projects": [], "pagination": {}}),
    )
    await _call("get_projects", {})
    await _call("get_projects", {})
    assert org_route.call_count == 1


@respx.mock
async def test_empty_list_renders_empty_message(tool_context):
    respx.get(f"{BASE}/organizations").mock(
        return_value=Response(200, json={"organizations": [], "pagination": {}}),
    )
    text = await _call("get_organizations", {})
    assert text == "No organizations found."


@respx.mock
async def test_get_tasks(tool_context):
    respx.get(f"{BASE}/projects/3/tasks").mock(
        return_value=Response(
            200, json={"tasks": [{"id": 7, "summary": "Do it", "status": "active"}], "pagination": {}}
        ),
    )
    text = await _call("get_tasks", {"project_id": 3})
    assert "Do it" in text


@respx.mock
async def test_get_members_uses_explicit_org(tool_context):
    respx.get(f"{BASE}/organizations/4/members").mock(
        return_value=Response(
            200,
            json={
                "members": [{"user_id": 5, "membership_role": "manager", "user": {"id": 5, "name": "Jo"}}],
                "pagination": {},
            },
        ),
    )
    text = await _call("get_members", {"organization_id": 4})
    assert "Jo" in text
    assert "manager" in text


@respx.mock
async def test_get_teams(tool_context):
    respx.get(f"{BASE}/organizations/4/teams").mock(
        return_value=Response(200, json={"teams": [{"id": 1, "name": "Core"}], "pagination": {}}),
    )
    text = await _call("get_teams", {"organization_id": 4})
    assert "Core" in text


@respx.mock
async def test_tool_surfaces_api_error_as_message(tool_context):
    respx.get(f"{BASE}/users/me").mock(return_value=Response(403, json={"error": "forbidden"}))
    text = await _call("get_current_user", {})
    assert text.startswith("Error:")
    assert "403" in text
