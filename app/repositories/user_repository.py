from app.domain.user import User
from app.hubstaff.errors import HubstaffAPIError
from app.repositories.base import Repository


class UserRepository(Repository):
    async def get_current_user(self) -> User:
        data = await self._client.request("GET", "/users/me")
        if not isinstance(data, dict) or "user" not in data:
            raise HubstaffAPIError("Unexpected Hubstaff response for /users/me", body=data)
        return User.model_validate(data["user"])
