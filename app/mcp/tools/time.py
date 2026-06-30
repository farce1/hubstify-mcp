from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from app.config import settings
from app.mcp.context import get_context
from app.mcp.support import bullet_list, hours, safe
from app.services.time_service import resolve_range
from app.services.timesheet_service import build_timesheet

time_router = FastMCP(name="Time")


def _today() -> date:
    # Resolve "today" in the configured timezone; Hubstaff buckets daily activity by org tz.
    return datetime.now(ZoneInfo(settings.default_timezone)).date()


@time_router.tool
@safe
async def get_time_entries(
    period: str = "this_week",
    organization_id: int | None = None,
    project_id: int | None = None,
) -> str:
    """List your tracked time per day. period: today, yesterday, this_week, last_week, this_month, last_month."""
    date_range = resolve_range(period, _today())
    ctx = get_context()
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    user_id = await ctx.current_user_id()
    project_ids = [project_id] if project_id is not None else None
    daily = await ctx.activities.daily(org_id, date_range, user_ids=[user_id], project_ids=project_ids)
    timesheet = build_timesheet(user_id, date_range, daily)
    names = await ctx.project_names(org_id)
    lines = [
        f"{line.day} · {_project_label(line.project_id, names)}: {hours(line.duration.seconds)}"
        for line in timesheet.lines
    ]
    header = (
        f"Time entries for {period} ({date_range.start}..{date_range.stop}) — total {hours(timesheet.total.seconds)}:"
    )
    return bullet_list(header, lines, f"No tracked time for {period}.")


@time_router.tool
@safe
async def get_timesheet(period: str = "this_week", organization_id: int | None = None) -> str:
    """Summarise tracked time per project. period: today, yesterday, this_week, last_week, this_month, last_month."""
    date_range = resolve_range(period, _today())
    ctx = get_context()
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    user_id = await ctx.current_user_id()
    timesheet = await ctx.timesheets.summary(org_id, user_id, date_range)
    names = await ctx.project_names(org_id)
    per_project: dict[int | None, int] = {}
    for line in timesheet.lines:
        per_project[line.project_id] = per_project.get(line.project_id, 0) + line.duration.seconds
    lines = [
        f"{_project_label(project_id, names)}: {hours(seconds)}"
        for project_id, seconds in sorted(per_project.items(), key=lambda item: -item[1])
    ]
    header = f"Timesheet for {period} ({date_range.start}..{date_range.stop}) — total {hours(timesheet.total.seconds)}:"
    return bullet_list(header, lines, f"No tracked time for {period}.")


def _project_label(project_id: int | None, names: dict[int, str]) -> str:
    if project_id is None:
        return "Unassigned"
    return names.get(project_id, f"project {project_id}")
