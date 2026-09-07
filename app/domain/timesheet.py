from collections import Counter
from datetime import date

from pydantic import BaseModel, Field

from app.domain.models import DateRange


class TimesheetLine(BaseModel):
    day: date
    project_id: int | None = None
    seconds: int


class Timesheet(BaseModel):
    """Derived view: tracked time grouped by day and project over a date range."""

    range: DateRange
    lines: list[TimesheetLine] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(line.seconds for line in self.lines)

    def by_project(self) -> list[tuple[int | None, int]]:
        """Collapse per-day lines into per-project totals, longest first."""
        totals: Counter[int | None] = Counter()
        for line in self.lines:
            totals[line.project_id] += line.seconds
        return totals.most_common()
