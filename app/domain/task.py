from datetime import datetime

from pydantic import Field

from app.domain.base import HubstaffModel


class Task(HubstaffModel):
    id: int
    summary: str
    details: str | None = None
    status: str | None = None
    project_id: int | None = None
    assignee_ids: list[int] = Field(default_factory=list)
    due_at: datetime | None = None
