from app.domain.base import HubstaffModel


class User(HubstaffModel):
    id: int
    name: str
    email: str | None = None
    time_zone: str | None = None
    status: str | None = None
