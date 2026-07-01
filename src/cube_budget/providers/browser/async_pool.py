"""Async Playwright browser pool."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from cube_budget.config.schema import ScraperConfig


class AsyncBrowserPool:
    """Manages async Playwright browser lifecycle with shared browser instance."""

    def __init__(self, config: ScraperConfig):
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            browser_type = getattr(self._playwright, self._config.browser)
            self._browser = await browser_type.launch(headless=self._config.headless)
            logger.debug(f"Async browser launched: {self._config.browser}")
        return self._browser

    @asynccontextmanager
    async def get_page(self) -> AsyncGenerator[Page, None]:
        browser = await self._ensure_browser()
        context: BrowserContext = await browser.new_context(
            user_agent=self._config.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
        )
        page = await context.new_page()
        page.set_default_timeout(self._config.timeout_ms)
        try:
            yield page
        finally:
            await context.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("Async browser pool closed")

    async def __aenter__(self) -> "AsyncBrowserPool":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
