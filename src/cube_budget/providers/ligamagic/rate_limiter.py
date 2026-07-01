"""Rate limiting for scraper requests."""

from __future__ import annotations

import asyncio
import random
import time

from cube_budget.config.schema import ScraperConfig


class RateLimiter:
    """Throttle sync requests with random delays."""

    def __init__(self, config: ScraperConfig):
        self._config = config
        self._last_request: float = 0.0

    def wait(self) -> None:
        min_delay, max_delay = self._config.page_load_delay_ms
        delay_ms = random.randint(min_delay, max_delay)
        elapsed = time.time() - self._last_request
        wait_s = max(0, delay_ms / 1000 - elapsed)
        if wait_s > 0:
            time.sleep(wait_s)
        self._last_request = time.time()


class AsyncRateLimiter:
    """
    Global async rate limiter shared across concurrent scrapers.

    Serializes navigation requests so parallel workers only overlap on
    in-page waits (JS loading), not on HTTP request rate.
    """

    def __init__(self, config: ScraperConfig):
        self._config = config
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            min_delay, max_delay = self._config.page_load_delay_ms
            delay_ms = random.randint(min_delay, max_delay)
            elapsed = time.time() - self._last_request
            wait_s = max(0, delay_ms / 1000 - elapsed)
            if wait_s > 0:
                await asyncio.sleep(wait_s)
            self._last_request = time.time()
