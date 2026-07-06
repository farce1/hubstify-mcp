from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from app.domain.timesheet import Timesheet
from app.mcp.context import Context, get_context
from app.mcp.support import bullet_list, hours, safe
from app.services.time_service import ensure_valid_period, resolve_range

time_router = FastMCP(name="Time")


def _today(tz: ZoneInfo) -> date:
    # Resolve "today" in the user's timezone; Hubstaff buckets daily activity by that zone.
    return datetime.now(tz).date()


async def _fetch_timesheet(
    period: str,
    organization_id: int | None,
    project_id: int | None = None,
) -> tuple[Context, int, Timesheet]:
    ensure_valid_period(period)  # reject a bad period before any I/O
    ctx = get_context()
    date_range = resolve_range(period, _today(await ctx.current_timezone()))
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    user_id = await ctx.current_user_id()
    project_ids = [project_id] if project_id is not None else None
    timesheet = await ctx.timesheets.summary(org_id, user_id, date_range, project_ids=project_ids)
    return ctx, org_id, timesheet


@time_router.tool
@safe
async def get_tracked_time(
    period: str = "this_week",
    organization_id: int | None = None,
    project_id: int | None = None,
) -> str:
    """List your tracked time per day. period: today, yesterday, this_week, last_week, this_month, last_month."""
    ctx, org_id, timesheet = await _fetch_timesheet(period, organization_id, project_id)
    names = await ctx.project_names(org_id)
    lines = [
        f"{line.day} · {_project_label(line.project_id, names)}: {hours(line.duration.seconds)}"
        for line in timesheet.lines
    ]
    return bullet_list(_header("Tracked time", period, timesheet), lines, f"No tracked time for {period}.")


@time_router.tool
@safe
async def get_timesheet(period: str = "this_week", organization_id: int | None = None) -> str:
    """Summarise tracked time per project. period: today, yesterday, this_week, last_week, this_month, last_month."""
    ctx, org_id, timesheet = await _fetch_timesheet(period, organization_id)
    names = await ctx.project_names(org_id)
    lines = [
        f"{_project_label(project_id, names)}: {hours(duration.seconds)}"
        for project_id, duration in timesheet.by_project()
    ]
    return bullet_list(_header("Timesheet", period, timesheet), lines, f"No tracked time for {period}.")


def _header(label: str, period: str, timesheet: Timesheet) -> str:
    span = f"{timesheet.range.start}..{timesheet.range.stop}"
    return f"{label} for {period} ({span}) — total {hours(timesheet.total.seconds)}:"


def _project_label(project_id: int | None, names: dict[int, str]) -> str:
    if project_id is None:
        return "Unassigned"
    return names.get(project_id, f"project {project_id}")
