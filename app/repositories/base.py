from app.hubstaff.client import HubstaffClient


class Repository:
    def __init__(self, client: HubstaffClient):
        self._client = client
