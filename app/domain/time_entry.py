from datetime import datetime

from pydantic import BaseModel, field_validator


class NewTimeEntry(BaseModel):
    """Input for creating a manual time entry (Hubstaff v2 is create-only)."""

    project_id: int
    start_time: datetime
    tracked: int
    task_id: int | None = None
    note: str | None = None
    billable: bool | None = None

    @field_validator("start_time")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("start_time must be timezone-aware so Hubstaff records the correct moment")
        return value

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "project_id": self.project_id,
            "start_time": self.start_time.isoformat(),
            "tracked": self.tracked,
        }
        if self.task_id is not None:
            payload["task_id"] = self.task_id
        if self.note is not None:
            payload["note"] = self.note
        if self.billable is not None:
            payload["billable"] = self.billable
        return payload
