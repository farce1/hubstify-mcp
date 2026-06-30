from datetime import date

import pytest
import respx
from httpx import Response

from app.domain.activity import DailyActivity
from app.domain.value_objects import DateRange
from app.repositories.activity_repository import ActivityRepository
from app.services.time_service import resolve_range
from app.services.timesheet_service import TimesheetService, build_timesheet

BASE = "https://api.hubstaff.com/v2"


class TestResolveRange:
    def test_today(self):
        today = date(2026, 6, 30)
        result = resolve_range("today", today)
        assert result.start == today
        assert result.stop == today

    def test_yesterday(self):
        result = resolve_range("yesterday", date(2026, 6, 30))
        assert result.start == date(2026, 6, 29)
        assert result.stop == date(2026, 6, 29)

    def test_this_week_is_monday_to_today(self):
        result = resolve_range("this week", date(2026, 6, 30))  # Tuesday; spaces + case normalised
        assert result.start == date(2026, 6, 29)  # Monday
        assert result.stop == date(2026, 6, 30)

    def test_this_week_when_today_is_monday_is_single_day(self):
        monday = date(2026, 6, 29)
        result = resolve_range("this_week", monday)
        assert result.start == monday
        assert result.stop == monday

    def test_last_week_is_full_previous_week(self):
        result = resolve_range("last_week", date(2026, 6, 30))
        assert result.start == date(2026, 6, 22)
        assert result.stop == date(2026, 6, 28)

    def test_this_month(self):
        today = date(2026, 6, 30)
        result = resolve_range("this_month", today)
        assert result.start == date(2026, 6, 1)
        assert result.stop == today

    def test_last_month(self):
        result = resolve_range("last_month", date(2026, 6, 15))
        assert result.start == date(2026, 5, 1)
        assert result.stop == date(2026, 5, 31)

    def test_last_month_crosses_year_boundary(self):
        result = resolve_range("last_month", date(2026, 1, 15))
        assert result.start == date(2025, 12, 1)
        assert result.stop == date(2025, 12, 31)

    def test_last_month_handles_leap_february(self):
        result = resolve_range("last_month", date(2024, 3, 10))
        assert result.start == date(2024, 2, 1)
        assert result.stop == date(2024, 2, 29)

    @pytest.mark.parametrize("period", ["today", "yesterday", "this_week", "last_week", "this_month", "last_month"])
    @pytest.mark.parametrize("today", [date(2026, 7, 31), date(2026, 1, 1), date(2024, 3, 1), date(2026, 2, 15)])
    def test_ranges_stay_within_daily_cap(self, period, today):
        assert resolve_range(period, today).days <= 31

    def test_unknown_period_raises(self):
        with pytest.raises(ValueError, match="fortnight"):
            resolve_range("fortnight", date(2026, 6, 30))


class TestBuildTimesheet:
    def test_groups_and_sums_by_day_and_project(self):
        date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2))
        activities = [
            DailyActivity(id=1, date=date(2026, 6, 1), user_id=7, project_id=1, tracked=3600),
            DailyActivity(id=2, date=date(2026, 6, 1), user_id=7, project_id=1, tracked=1800),
            DailyActivity(id=3, date=date(2026, 6, 2), user_id=7, project_id=2, tracked=900),
        ]
        timesheet = build_timesheet(7, date_range, activities)
        assert timesheet.total.seconds == 6300
        assert len(timesheet.lines) == 2
        assert timesheet.lines[0].duration.seconds == 5400

    def test_sorts_by_day_then_project(self):
        date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2))
        activities = [
            DailyActivity(id=1, date=date(2026, 6, 2), user_id=7, project_id=2, tracked=100),
            DailyActivity(id=2, date=date(2026, 6, 1), user_id=7, project_id=5, tracked=200),
            DailyActivity(id=3, date=date(2026, 6, 1), user_id=7, project_id=1, tracked=300),
        ]
        timesheet = build_timesheet(7, date_range, activities)
        ordered = [(line.day, line.project_id) for line in timesheet.lines]
        assert ordered == [(date(2026, 6, 1), 1), (date(2026, 6, 1), 5), (date(2026, 6, 2), 2)]

    def test_empty(self):
        date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 1))
        timesheet = build_timesheet(7, date_range, [])
        assert timesheet.lines == []
        assert timesheet.total.seconds == 0

    def test_keeps_unassigned_project_as_distinct_line(self):
        date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 1))
        activities = [
            DailyActivity(id=1, date=date(2026, 6, 1), user_id=7, project_id=3, tracked=600),
            DailyActivity(id=2, date=date(2026, 6, 1), user_id=7, project_id=None, tracked=300),
        ]
        timesheet = build_timesheet(7, date_range, activities)
        assert len(timesheet.lines) == 2
        assert timesheet.lines[0].project_id is None  # None sorts before positive ids
        assert timesheet.lines[1].project_id == 3


@respx.mock
async def test_timesheet_service_summary_fetches_and_assembles(api):
    respx.get(f"{BASE}/organizations/9/activities/daily").mock(
        return_value=Response(
            200,
            json={
                "daily_activities": [{"id": 1, "date": "2026-06-01", "user_id": 7, "project_id": 1, "tracked": 3600}],
                "pagination": {},
            },
        ),
    )
    date_range = DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2))
    timesheet = await TimesheetService(ActivityRepository(api)).summary(9, 7, date_range)
    assert timesheet.user_id == 7
    assert timesheet.total.seconds == 3600
