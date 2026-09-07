from app.domain.base import HubstaffModel


class Task(HubstaffModel):
    id: int
    summary: str
    status: str | None = None
    project_id: int | None = None
