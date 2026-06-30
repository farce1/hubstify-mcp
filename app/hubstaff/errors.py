class HubstaffError(Exception):
    """Base error for Hubstaff integration failures."""


class HubstaffAuthError(HubstaffError):
    """Authentication or token-refresh failed."""
