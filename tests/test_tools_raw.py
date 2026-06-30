import respx
from httpx import Response

from tests._helpers import BASE
from tests._helpers import call_tool as _call


@respx.mock
async def test_hubstaff_get_allows_listed_prefix(tool_context):
    respx.get(f"{BASE}/organizations/9/screenshots").mock(
        return_value=Response(200, json={"screenshots": [{"id": 1}]}),
    )
    text = await _call("hubstaff_get", {"path": "organizations/9/screenshots"})
    assert "screenshots" in text


@respx.mock
async def test_hubstaff_get_strips_leading_slash(tool_context):
    route = respx.get(f"{BASE}/projects/5").mock(return_value=Response(200, json={"project": {"id": 5}}))
    await _call("hubstaff_get", {"path": "/projects/5"})
    assert route.called


@respx.mock
async def test_hubstaff_get_passes_params(tool_context):
    route = respx.get(f"{BASE}/users/me").mock(return_value=Response(200, json={"user": {"id": 1}}))
    await _call("hubstaff_get", {"path": "users/me", "params": {"include": "projects"}})
    assert "include=projects" in str(route.calls.last.request.url)


async def test_hubstaff_get_rejects_disallowed_prefix(tool_context):
    text = await _call("hubstaff_get", {"path": "webhooks"})
    assert text.startswith("Error:")


@respx.mock
async def test_hubstaff_get_blocks_path_traversal(tool_context):
    webhooks = respx.get(f"{BASE}/webhooks").mock(return_value=Response(200, json={}))
    text = await _call("hubstaff_get", {"path": "users/../webhooks"})
    assert text.startswith("Error:")
    assert not webhooks.called


async def test_hubstaff_get_blocks_encoded_traversal(tool_context):
    text = await _call("hubstaff_get", {"path": "organizations/..%2f..%2ffoo"})
    assert text.startswith("Error:")
