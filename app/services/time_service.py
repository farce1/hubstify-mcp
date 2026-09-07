from collections.abc import Callable
from datetime import date, timedelta

from app.domain.value_objects import DateRange

# Current periods are to-date (this_week = Monday..today); past periods are the full
# calendar span. Every range stays within Hubstaff's 31-day daily-activity cap.
_PERIODS: dict[str, Callable[[date], DateRange]] = {
    "today": lambda d: DateRange(start=d, stop=d),
    "yesterday": lambda d: DateRange(start=d - timedelta(days=1), stop=d - timedelta(days=1)),
    "this_week": lambda d: DateRange(start=d - timedelta(days=d.weekday()), stop=d),
    "last_week": lambda d: DateRange(
        start=d - timedelta(days=d.weekday() + 7), stop=d - timedelta(days=d.weekday() + 1)
    ),
    "this_month": lambda d: DateRange(start=d.replace(day=1), stop=d),
    "last_month": lambda d: DateRange(
        start=(d.replace(day=1) - timedelta(days=1)).replace(day=1),
        stop=d.replace(day=1) - timedelta(days=1),
    ),
}


def parse_period(period: str) -> Callable[[date], DateRange]:
    """Validate a human period ("today", "this week", ...) and return its range builder.

    Returning the builder lets callers reject a bad period before doing any I/O
    (resolving "today" needs the user's timezone, which costs an API call).
    """
    key = period.strip().lower().replace(" ", "_")
    if key not in _PERIODS:
        raise ValueError(f"Unknown period {period!r}. Use one of: {', '.join(_PERIODS)}.")
    return _PERIODS[key]
