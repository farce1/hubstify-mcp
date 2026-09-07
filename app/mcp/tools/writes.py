from datetime import datetime

from fastmcp import FastMCP

from app.domain.time_entry import NewTimeEntry
from app.hubstaff import api
from app.mcp.context import Context, get_context
from app.mcp.support import hours as format_hours
from app.mcp.support import safe

writes_router = FastMCP(name="Writes")


@writes_router.tool
@safe
async def log_time(
    project_id: int,
    hours: float,
    start_time: str | None = None,
    task_id: int | None = None,
    note: str | None = None,
    billable: bool | None = None,
) -> str:
    """Create a manual time entry for yourself (cannot be edited or deleted afterward via the API).

    hours is decimal (e.g. 1.5); start_time is optional ISO 8601, defaults to now.
    """
    if hours <= 0:
        raise ValueError("hours must be greater than 0")
    seconds = round(hours * 3600)
    ctx = get_context()
    moment = await _start_moment(start_time, ctx)
    entry = NewTimeEntry(
        project_id=project_id,
        start_time=moment,
        tracked=seconds,
        task_id=task_id,
        note=note,
        billable=billable,
    )
    user_id = await ctx.current_user_id()
    await api.create_time_entry(ctx.client, user_id, entry)
    return f"Logged {format_hours(seconds)} to project {project_id} starting {moment.isoformat()}."


@writes_router.tool
@safe
async def create_task(
    project_id: int,
    summary: str,
    details: str | None = None,
    assignee_ids: list[int] | None = None,
) -> str:
    """Create a task in a project."""
    task = await api.create_task(get_context().client, project_id, summary, details, assignee_ids)
    return f"Created task '{task.summary}' (id {task.id}) in project {project_id}."


async def _start_moment(start_time: str | None, ctx: Context) -> datetime:
    # Parse first so malformed input fails fast, before any timezone lookup.
    if not start_time:
        return datetime.now(await ctx.current_timezone())
    moment = datetime.fromisoformat(start_time)
    if moment.tzinfo:
        return moment
    return moment.replace(tzinfo=await ctx.current_timezone())
