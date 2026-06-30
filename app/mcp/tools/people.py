from fastmcp import FastMCP

from app.domain.member import OrganizationMember
from app.mcp.context import get_context
from app.mcp.support import bullet_list, safe

people_router = FastMCP(name="People")


@people_router.tool
@safe
async def get_members(organization_id: int | None = None) -> str:
    """List members of an organization (defaults to your primary one)."""
    ctx = get_context()
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    members = await ctx.members.list_members(org_id)
    lines = [_member_line(member) for member in members]
    return bullet_list(f"Members of organization {org_id}:", lines, "No members found.")


@people_router.tool
@safe
async def get_teams(organization_id: int | None = None) -> str:
    """List teams in an organization (defaults to your primary one)."""
    ctx = get_context()
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    teams = await ctx.teams.list_teams(org_id)
    lines = [f"{team.name} (id {team.id})" for team in teams]
    return bullet_list(f"Teams in organization {org_id}:", lines, "No teams found.")


def _member_line(member: OrganizationMember) -> str:
    name = member.user.name if member.user else f"user {member.user_id}"
    role = f", {member.membership_role}" if member.membership_role else ""
    return f"{name} (id {member.user_id}{role})"
