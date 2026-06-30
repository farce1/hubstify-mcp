from fastmcp import FastMCP

from app.mcp.context import get_context
from app.mcp.support import bullet_list, safe

identity_router = FastMCP(name="Identity")


@identity_router.tool
@safe
async def get_current_user() -> str:
    """Get the authenticated Hubstaff user (you)."""
    user = await get_context().users.get_current_user()
    email = f", {user.email}" if user.email else ""
    return f"You are {user.name} (id {user.id}{email})."


@identity_router.tool
@safe
async def get_organizations() -> str:
    """List the Hubstaff organizations you belong to."""
    organizations = await get_context().organizations.list_organizations()
    lines = [f"{org.name} (id {org.id})" for org in organizations]
    return bullet_list("Organizations:", lines, "No organizations found.")
