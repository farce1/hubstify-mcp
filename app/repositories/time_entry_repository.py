from typing import Any

from app.domain.time_entry import NewTimeEntry
from app.repositories.base import Repository


class TimeEntryRepository(Repository):
    async def create(self, user_id: int, entry: NewTimeEntry) -> Any:
        return await self._client.request("POST", f"/users/{user_id}/time_entries", json=entry.to_payload())
