from app.domain.task import Task
from app.repositories.base import Repository


class TaskRepository(Repository):
    async def list_tasks(self, project_id: int, status: str | None = None) -> list[Task]:
        items = await self._client.get_list(f"/projects/{project_id}/tasks", "tasks", params={"status": status})
        return [Task.model_validate(item) for item in items]

    async def create(
        self,
        project_id: int,
        summary: str,
        details: str | None = None,
        assignee_ids: list[int] | None = None,
    ) -> Task:
        body: dict[str, object] = {"summary": summary}
        if details is not None:
            body["details"] = details
        if assignee_ids is not None:
            body["assignee_ids"] = assignee_ids
        data = await self._client.request("POST", f"/projects/{project_id}/tasks", json=body)
        # Create response envelope is not firmly documented; tolerate flat or {"task": ...}.
        payload = data.get("task", data) if isinstance(data, dict) else data
        return Task.model_validate(payload)
