from app.domain.base import HubstaffModel


class Team(HubstaffModel):
    id: int
    name: str
