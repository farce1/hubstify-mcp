class HubstaffError(Exception):
    """Base error for Hubstaff integration failures."""


class HubstaffAuthError(HubstaffError):
    """Authentication or token-refresh failed."""


class HubstaffAPIError(HubstaffError):
    """A Hubstaff API request failed."""

    def __init__(self, message: str, *, status: int | None = None, body: object = None):
        super().__init__(message)
        self.status = status
        self.body = body


class HubstaffRateLimitError(HubstaffAPIError):
    """Rate limit exceeded and retries were exhausted."""
