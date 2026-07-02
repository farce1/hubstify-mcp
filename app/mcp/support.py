import functools
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from fastmcp.exceptions import ToolError

from app.domain.value_objects import Duration
from app.hubstaff.errors import HubstaffError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Surface expected Hubstaff/input failures as a ToolError (isError=true).

    Hubstaff errors are expected. Other ValueErrors (bad user input, or an
    unexpected response shape) are logged before being surfaced, so they are
    diagnosable rather than silently masked. The readable message is preserved.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except HubstaffError as exc:
            raise ToolError(str(exc)) from exc
        except ValueError as exc:
            logger.warning("Tool %s failed: %s", getattr(func, "__name__", "tool"), exc)
            raise ToolError(str(exc)) from exc

    return wrapper


def hours(seconds: int) -> str:
    return Duration(seconds=seconds).human


def bullet_list(header: str, lines: list[str], empty: str) -> str:
    if not lines:
        return empty
    return "\n".join([header, *(f"- {line}" for line in lines)])
