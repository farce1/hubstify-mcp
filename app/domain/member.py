from app.domain.base import HubstaffModel
from app.domain.user import User


class OrganizationMember(HubstaffModel):
    user_id: int
    membership_role: str | None = None
    membership_status: str | None = None
    user: User | None = None
