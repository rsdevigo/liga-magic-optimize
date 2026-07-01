"""External providers."""

from cube_budget.providers.browser.async_pool import AsyncBrowserPool
from cube_budget.providers.browser.pool import BrowserPool
from cube_budget.providers.ligamagic.scraper import LigaMagicScraper

__all__ = ["AsyncBrowserPool", "BrowserPool", "LigaMagicScraper"]
