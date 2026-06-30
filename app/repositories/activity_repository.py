from app.domain.activity import DailyActivity
from app.domain.value_objects import DateRange
from app.repositories.base import Repository


class ActivityRepository(Repository):
    async def daily(
        self,
        organization_id: int,
        date_range: DateRange,
        user_ids: list[int] | None = None,
        project_ids: list[int] | None = None,
    ) -> list[DailyActivity]:
        params = {
            "date[start]": date_range.start.isoformat(),
            "date[stop]": date_range.stop.isoformat(),
            "user_ids": user_ids,
            "project_ids": project_ids,
        }
        items = await self._client.get_list(
            f"/organizations/{organization_id}/activities/daily",
            "daily_activities",
            params=params,
        )
        return [DailyActivity.model_validate(item) for item in items]
