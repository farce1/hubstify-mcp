from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.domain.models import DailyActivity, DateRange, OrganizationMember, Project
from app.domain.time_entry import NewTimeEntry
from app.domain.timesheet import Timesheet, TimesheetLine


def test_model_ignores_unknown_fields():
    project = Project.model_validate(
        {"id": 1, "name": "Acme", "status": "active", "billable": True, "unmapped": "x"},
    )
    assert (project.id, project.name, project.billable) == (1, "Acme", True)


def test_member_parses_nested_user():
    member = OrganizationMember.model_validate(
        {"user_id": 7, "membership_role": "user", "user": {"id": 7, "name": "Jo"}},
    )
    assert member.user is not None
    assert member.user.name == "Jo"


def test_daily_activity_maps_tracked_seconds():
    activity = DailyActivity.model_validate(
        {"id": 1, "date": "2026-06-30", "user_id": 7, "project_id": 3, "tracked": 3600},
    )
    assert activity.tracked == 3600
    assert activity.date == date(2026, 6, 30)


def test_new_time_entry_rejects_naive_start_time():
    with pytest.raises(ValidationError):
        NewTimeEntry(project_id=3, start_time=datetime(2026, 6, 30, 9, 0), tracked=7200)


def test_timesheet_total_sums_lines():
    timesheet = Timesheet(
        range=DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2)),
        lines=[
            TimesheetLine(day=date(2026, 6, 1), project_id=1, seconds=3600),
            TimesheetLine(day=date(2026, 6, 2), project_id=2, seconds=1800),
        ],
    )
    assert timesheet.total == 5400


def test_timesheet_by_project_aggregates_and_sorts_by_duration_desc():
    timesheet = Timesheet(
        range=DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2)),
        lines=[
            TimesheetLine(day=date(2026, 6, 1), project_id=1, seconds=600),
            TimesheetLine(day=date(2026, 6, 2), project_id=1, seconds=600),
            TimesheetLine(day=date(2026, 6, 1), project_id=2, seconds=3600),
        ],
    )
    assert timesheet.by_project() == [(2, 3600), (1, 1200)]


def test_date_range_allows_a_single_day():
    date_range = DateRange(start=date(2026, 6, 30), stop=date(2026, 6, 30))
    assert date_range.start == date_range.stop


def test_start_after_stop_is_rejected():
    with pytest.raises(ValidationError):
        DateRange(start=date(2026, 6, 7), stop=date(2026, 6, 1))
