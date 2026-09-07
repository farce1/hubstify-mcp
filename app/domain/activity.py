from datetime import date

from app.domain.base import HubstaffModel


class DailyActivity(HubstaffModel):
    """Per-day aggregated tracked time."""

    date: date
    project_id: int | None = None
    tracked: int = 0
