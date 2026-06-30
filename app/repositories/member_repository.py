from app.domain.member import OrganizationMember
from app.repositories.base import Repository


class MemberRepository(Repository):
    async def list_members(self, organization_id: int) -> list[OrganizationMember]:
        items = await self._client.get_list(
            f"/organizations/{organization_id}/members",
            "members",
            params={"include": "users"},
        )
        return [OrganizationMember.model_validate(item) for item in items]
