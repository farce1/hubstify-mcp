from datetime import date, timedelta

from app.domain.value_objects import DateRange

_PERIODS = ("today", "yesterday", "this_week", "last_week", "this_month", "last_month")


def resolve_range(period: str, today: date) -> DateRange:
    """Turn a human period ("today", "this week", "last month", ...) into a DateRange.

    Current periods are to-date (e.g. this_week = Monday..today); past periods are
    the full calendar span. All resolved ranges stay within the 31-day daily-activity cap.
    """
    key = period.strip().lower().replace(" ", "_")
    if key == "today":
        return DateRange(start=today, stop=today)
    if key == "yesterday":
        yesterday = today - timedelta(days=1)
        return DateRange(start=yesterday, stop=yesterday)
    if key == "this_week":
        return DateRange(start=today - timedelta(days=today.weekday()), stop=today)
    if key == "last_week":
        last_monday = today - timedelta(days=today.weekday() + 7)
        return DateRange(start=last_monday, stop=last_monday + timedelta(days=6))
    if key == "this_month":
        return DateRange(start=today.replace(day=1), stop=today)
    if key == "last_month":
        last_day_prev = today.replace(day=1) - timedelta(days=1)
        return DateRange(start=last_day_prev.replace(day=1), stop=last_day_prev)
    raise ValueError(f"Unknown period {period!r}. Use one of: {', '.join(_PERIODS)}.")
