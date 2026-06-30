from app.domain.organization import Organization
from app.repositories.base import Repository


class OrganizationRepository(Repository):
    async def list_organizations(self) -> list[Organization]:
        items = await self._client.get_list("/organizations", "organizations")
        return [Organization.model_validate(item) for item in items]
