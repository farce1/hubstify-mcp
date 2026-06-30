from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.activity import DailyActivity
from app.domain.member import OrganizationMember
from app.domain.project import Project
from app.domain.time_entry import NewTimeEntry
from app.domain.timesheet import Timesheet, TimesheetLine
from app.domain.value_objects import DateRange, Duration


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


def test_daily_activity_parses_billable_as_seconds():
    activity = DailyActivity.model_validate(
        {"id": 1, "date": "2026-06-30", "user_id": 7, "project_id": 3, "tracked": 28800, "billable": 28800},
    )
    assert activity.billable_seconds == 28800


def test_new_time_entry_payload_omits_unset_optionals():
    entry = NewTimeEntry(
        project_id=3,
        start_time=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        tracked=7200,
    )
    assert entry.to_payload() == {
        "project_id": 3,
        "start_time": "2026-06-30T09:00:00+00:00",
        "tracked": 7200,
    }


def test_new_time_entry_payload_includes_set_optionals():
    entry = NewTimeEntry(
        project_id=3,
        start_time=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        tracked=7200,
        task_id=11,
        note="API integration",
        billable=True,
    )
    payload = entry.to_payload()
    assert payload["task_id"] == 11
    assert payload["note"] == "API integration"
    assert payload["billable"] is True


def test_new_time_entry_payload_keeps_billable_false():
    entry = NewTimeEntry(
        project_id=3,
        start_time=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        tracked=7200,
        billable=False,
    )
    assert entry.to_payload()["billable"] is False


def test_new_time_entry_rejects_naive_start_time():
    with pytest.raises(ValidationError):
        NewTimeEntry(project_id=3, start_time=datetime(2026, 6, 30, 9, 0), tracked=7200)


def test_timesheet_total_sums_line_durations():
    timesheet = Timesheet(
        range=DateRange(start=date(2026, 6, 1), stop=date(2026, 6, 2)),
        user_id=7,
        lines=[
            TimesheetLine(day=date(2026, 6, 1), project_id=1, duration=Duration(seconds=3600)),
            TimesheetLine(day=date(2026, 6, 2), project_id=2, duration=Duration(seconds=1800)),
        ],
    )
    assert timesheet.total.seconds == 5400
