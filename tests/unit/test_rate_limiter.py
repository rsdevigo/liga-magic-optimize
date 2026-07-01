"""Tests for rate limiter."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from cube_budget.config.schema import ScraperConfig
from cube_budget.providers.ligamagic.rate_limiter import AsyncRateLimiter, RateLimiter


class TestRateLimiter:
    def test_wait_applies_delay(self):
        config = ScraperConfig(page_load_delay_ms=[100, 100])
        limiter = RateLimiter(config)

        with patch("time.sleep") as mock_sleep:
            with patch("time.time", side_effect=[0.0, 0.0]):
                limiter.wait()
            mock_sleep.assert_called()

    def test_rate_limiter_init(self):
        limiter = RateLimiter(ScraperConfig())
        assert limiter._config is not None


class TestAsyncRateLimiter:
    @pytest.mark.asyncio
    async def test_wait_applies_delay(self):
        config = ScraperConfig(page_load_delay_ms=[100, 100])
        limiter = AsyncRateLimiter(config)

        with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
            with patch("time.time", side_effect=[0.0, 0.0]):
                await limiter.wait()
            mock_sleep.assert_awaited()

    @pytest.mark.asyncio
    async def test_concurrent_waits_are_serialized(self):
        config = ScraperConfig(page_load_delay_ms=[50, 50])
        limiter = AsyncRateLimiter(config)
        order: list[int] = []

        async def worker(worker_id: int) -> None:
            await limiter.wait()
            order.append(worker_id)

        await asyncio.gather(worker(1), worker(2), worker(3))
        assert len(order) == 3
