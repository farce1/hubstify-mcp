from collections import Counter
from datetime import date

from app.domain.activity import DailyActivity
from app.domain.timesheet import Timesheet, TimesheetLine
from app.domain.value_objects import DateRange
from app.hubstaff import api
from app.hubstaff.client import HubstaffClient


def build_timesheet(user_id: int, date_range: DateRange, activities: list[DailyActivity]) -> Timesheet:
    """Group daily activities by day and project into a Timesheet projection."""
    totals: Counter[tuple[date, int | None]] = Counter()
    for activity in activities:
        totals[(activity.date, activity.project_id)] += activity.tracked
    lines = [
        TimesheetLine(day=day, project_id=project_id, seconds=seconds)
        for (day, project_id), seconds in sorted(totals.items(), key=lambda item: (item[0][0], item[0][1] or 0))
    ]
    return Timesheet(range=date_range, user_id=user_id, lines=lines)


async def fetch_timesheet(
    client: HubstaffClient,
    organization_id: int,
    user_id: int,
    date_range: DateRange,
    project_ids: list[int] | None = None,
) -> Timesheet:
    daily = await api.daily_activities(
        client,
        organization_id,
        date_range,
        user_ids=[user_id],
        project_ids=project_ids,
    )
    return build_timesheet(user_id, date_range, daily)
