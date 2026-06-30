import functools
import logging
from collections.abc import Awaitable, Callable

from app.domain.value_objects import Duration
from app.hubstaff.errors import HubstaffError

logger = logging.getLogger(__name__)


def safe(func: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
    """Turn expected Hubstaff/input failures into a readable tool message.

    Hubstaff errors are expected and returned as-is. Other ValueErrors
    (bad user input, or an unexpected response shape) are logged before being
    surfaced, so they are diagnosable rather than silently masked.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        try:
            return await func(*args, **kwargs)
        except HubstaffError as exc:
            return f"Error: {exc}"
        except ValueError as exc:
            logger.warning("Tool %s returned an error: %s", getattr(func, "__name__", "tool"), exc)
            return f"Error: {exc}"

    return wrapper


def hours(seconds: int) -> str:
    return Duration(seconds=seconds).human


def bullet_list(header: str, lines: list[str], empty: str) -> str:
    if not lines:
        return empty
    return "\n".join([header, *(f"- {line}" for line in lines)])
