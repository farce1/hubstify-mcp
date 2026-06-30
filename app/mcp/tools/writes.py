from datetime import datetime
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from app.config import settings
from app.domain.time_entry import NewTimeEntry
from app.domain.value_objects import Duration
from app.mcp.context import get_context
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
    duration = Duration.from_hours(hours)
    moment = _start_moment(start_time)
    entry = NewTimeEntry(
        project_id=project_id,
        start_time=moment,
        tracked=duration.seconds,
        task_id=task_id,
        note=note,
        billable=billable,
    )
    ctx = get_context()
    user_id = await ctx.current_user_id()
    await ctx.time_entries.create(user_id, entry)
    return f"Logged {duration.human} to project {project_id} starting {moment.isoformat()}."


@writes_router.tool
@safe
async def create_task(
    project_id: int,
    summary: str,
    details: str | None = None,
    assignee_ids: list[int] | None = None,
) -> str:
    """Create a task in a project."""
    task = await get_context().tasks.create(project_id, summary, details, assignee_ids)
    return f"Created task '{task.summary}' (id {task.id}) in project {project_id}."


def _start_moment(start_time: str | None) -> datetime:
    tz = ZoneInfo(settings.default_timezone)
    if not start_time:
        return datetime.now(tz)
    moment = datetime.fromisoformat(start_time)
    return moment if moment.tzinfo else moment.replace(tzinfo=tz)
