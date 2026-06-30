from datetime import date

from app.domain.activity import DailyActivity
from app.domain.timesheet import Timesheet, TimesheetLine
from app.domain.value_objects import DateRange, Duration
from app.repositories.activity_repository import ActivityRepository


def build_timesheet(user_id: int, date_range: DateRange, activities: list[DailyActivity]) -> Timesheet:
    """Group daily activities by day and project into a Timesheet projection."""
    totals: dict[tuple[date, int | None], int] = {}
    for activity in activities:
        key = (activity.date, activity.project_id)
        totals[key] = totals.get(key, 0) + activity.tracked
    lines = [
        TimesheetLine(day=day, project_id=project_id, duration=Duration(seconds=seconds))
        for (day, project_id), seconds in sorted(totals.items(), key=lambda item: (item[0][0], item[0][1] or 0))
    ]
    return Timesheet(range=date_range, user_id=user_id, lines=lines)


class TimesheetService:
    def __init__(self, activities: ActivityRepository):
        self._activities = activities

    async def summary(self, organization_id: int, user_id: int, date_range: DateRange) -> Timesheet:
        daily = await self._activities.daily(organization_id, date_range, user_ids=[user_id])
        return build_timesheet(user_id, date_range, daily)
