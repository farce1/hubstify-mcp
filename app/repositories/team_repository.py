from app.domain.team import Team
from app.repositories.base import Repository


class TeamRepository(Repository):
    async def list_teams(self, organization_id: int) -> list[Team]:
        items = await self._client.get_list(f"/organizations/{organization_id}/teams", "teams")
        return [Team.model_validate(item) for item in items]
