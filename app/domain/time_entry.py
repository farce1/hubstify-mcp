from datetime import datetime

from pydantic import BaseModel, field_serializer, field_validator


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

    @field_serializer("start_time")
    def _serialize_start_time(self, value: datetime) -> str:
        # Hubstaff has only ever been sent offsets, never "Z"; keep the wire format
        # identical to what these irreversible writes have always used.
        return value.isoformat()
