from app.domain.base import HubstaffModel


class Organization(HubstaffModel):
    id: int
    name: str
    status: str | None = None
