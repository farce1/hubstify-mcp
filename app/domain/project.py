from app.domain.base import HubstaffModel


class Project(HubstaffModel):
    id: int
    name: str
    status: str | None = None
    billable: bool | None = None
    client_id: int | None = None
