from datetime import date

from pydantic import BaseModel, Field

from app.domain.value_objects import DateRange, Duration


class TimesheetLine(BaseModel):
    day: date
    project_id: int | None = None
    duration: Duration


class Timesheet(BaseModel):
    """Derived view: tracked time grouped by day and project over a date range."""

    range: DateRange
    user_id: int
    lines: list[TimesheetLine] = Field(default_factory=list)

    @property
    def total(self) -> Duration:
        return Duration(seconds=sum(line.duration.seconds for line in self.lines))
