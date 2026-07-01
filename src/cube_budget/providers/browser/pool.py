"""Playwright browser pool."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from cube_budget.config.schema import ScraperConfig


class BrowserPool:
    """Manages Playwright browser lifecycle."""

    def __init__(self, config: ScraperConfig):
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def _ensure_browser(self) -> Browser:
        if self._browser is None or not self._browser.is_connected():
            self._playwright = sync_playwright().start()
            browser_type = getattr(self._playwright, self._config.browser)
            self._browser = browser_type.launch(headless=self._config.headless)
            logger.debug(f"Browser launched: {self._config.browser}")
        return self._browser

    @contextmanager
    def get_page(self) -> Generator[Page, None, None]:
        browser = self._ensure_browser()
        context: BrowserContext = browser.new_context(
            user_agent=self._config.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
        )
        page = context.new_page()
        page.set_default_timeout(self._config.timeout_ms)
        try:
            yield page
        finally:
            context.close()

    def close(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.debug("Browser pool closed")

    def __enter__(self) -> "BrowserPool":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
