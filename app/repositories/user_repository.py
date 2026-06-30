from app.domain.user import User
from app.repositories.base import Repository


class UserRepository(Repository):
    async def get_current_user(self) -> User:
        data = await self._client.request("GET", "/users/me")
        return User.model_validate(data["user"])
