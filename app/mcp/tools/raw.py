import json

from fastmcp import FastMCP

from app.mcp.context import get_context
from app.mcp.support import safe

raw_router = FastMCP(name="Raw")

_ALLOWED_PREFIXES = ("organizations/", "users/", "projects/")
_MAX_OUTPUT = 6000


@raw_router.tool
@safe
async def hubstaff_get(path: str, params: dict | None = None) -> str:
    """Read-only GET for Hubstaff v2 endpoints without a dedicated tool.

    path must start with organizations/, users/, or projects/.
    """
    normalized = path.strip().lstrip("/")
    lowered = normalized.lower()
    # Reject traversal: the HTTP client (httpx) collapses ".." segments after this
    # check, so an unguarded "users/../webhooks" would escape the allow-list.
    if (
        not normalized.startswith(_ALLOWED_PREFIXES)
        or ".." in normalized
        or "%2e" in lowered
        or "%2f" in lowered
        or "\\" in normalized
    ):
        raise ValueError(f"path must start with one of {', '.join(_ALLOWED_PREFIXES)} and not contain path traversal")
    data = await get_context().client.request("GET", f"/{normalized}", params=params)
    text = json.dumps(data, indent=2, default=str)
    if len(text) > _MAX_OUTPUT:
        return f"{text[:_MAX_OUTPUT]}\n… (truncated, {len(text)} chars total)"
    return text
