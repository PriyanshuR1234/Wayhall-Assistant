"""
Exponential-backoff retry decorator for Gemini API calls.
Retries on common transient errors (rate limits, timeouts, network blips).
"""

import asyncio
import functools
import time
from typing import Callable, Type, Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Errors that warrant a retry
_RETRYABLE_SUBSTRINGS = (
    "429",
    "rate_limit",
    "ratelimit",
    "resource_exhausted",
    "resourceexhausted",
    "quota",
    "timeout",
    "timed out",
    "connection",
    "503",
    "502",
)


def _is_retryable(exc: Exception) -> bool:
    msg = f"{str(exc)} {exc.__class__.__name__}".lower()
    return any(s in msg for s in _RETRYABLE_SUBSTRINGS)


def retry_sync(
    attempts: int = 4,
    base_delay: float = 3.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for synchronous functions — retries with exponential backoff."""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if not _is_retryable(exc) or attempt == attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Retryable error on attempt %d/%d — sleeping %.1fs | %s",
                        attempt,
                        attempts,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def retry_async(
    attempts: int = 3,
    base_delay: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for async functions — retries with exponential backoff."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if not _is_retryable(exc) or attempt == attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Retryable error on attempt %d/%d — sleeping %.1fs | %s",
                        attempt,
                        attempts,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
