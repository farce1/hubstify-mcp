from datetime import date, datetime

from app.domain.base import HubstaffModel


class _ActivityBase(HubstaffModel):
    id: int
    date: date
    user_id: int
    project_id: int | None = None
    task_id: int | None = None
    tracked: int = 0
    keyboard: int | None = None
    mouse: int | None = None
    overall: int | None = None
    billable: bool | None = None


class Activity(_ActivityBase):
    """A 10-minute tracked-time block."""

    starts_at: datetime | None = None


class DailyActivity(_ActivityBase):
    """Per-day aggregated tracked time."""
