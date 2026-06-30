from app.domain.project import Project
from app.repositories.base import Repository


class ProjectRepository(Repository):
    async def list_projects(self, organization_id: int, status: str | None = None) -> list[Project]:
        # Omitting status returns Hubstaff's default (active projects only).
        items = await self._client.get_list(
            f"/organizations/{organization_id}/projects",
            "projects",
            params={"status": status},
        )
        return [Project.model_validate(item) for item in items]
