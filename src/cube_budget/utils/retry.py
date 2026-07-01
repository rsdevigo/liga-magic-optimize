"""Retry decorator with exponential backoff."""

from __future__ import annotations

import asyncio
import random
import time
from functools import wraps
from typing import Callable, TypeVar

from loguru import logger

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry a function with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    if jitter:
                        delay *= 0.5 + random.random()
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry an async function with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    if jitter:
                        delay *= 0.5 + random.random()
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
            raise last_exc  # type: ignore

        return wrapper

    return decorator
