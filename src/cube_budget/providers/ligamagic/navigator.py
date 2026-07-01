"""LigaMagic browser navigation (async Playwright)."""

from __future__ import annotations

import random
import time
from collections.abc import AsyncIterator
from urllib.parse import quote_plus, urljoin

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from cube_budget.config.schema import FiltersConfig, ScraperConfig
from cube_budget.core.exceptions import CaptchaDetectedError
from cube_budget.providers.ligamagic import selectors as sel
from cube_budget.providers.ligamagic.parser import LigaMagicParser
from cube_budget.providers.ligamagic.rate_limiter import AsyncRateLimiter
from cube_budget.utils.retry import async_retry


class LigaMagicNavigator:
    """Handles async Playwright navigation on LigaMagic."""

    def __init__(
        self,
        config: ScraperConfig,
        filters: FiltersConfig,
        parser: LigaMagicParser | None = None,
        rate_limiter: AsyncRateLimiter | None = None,
    ):
        self._config = config
        self._filters = filters
        self._parser = parser or LigaMagicParser()
        self._rate_limiter = rate_limiter or AsyncRateLimiter(config)
        self._base_url = config.base_url.rstrip("/")

    @async_retry(max_attempts=3, base_delay=2.0, jitter=True, exceptions=(PlaywrightTimeout, Exception))
    async def navigate_to_card(self, page: Page, card_name: str) -> str:
        """Navigate to card page and return final HTML."""
        await self._rate_limiter.wait()
        search_url = f"{self._base_url}/?view=cards/search&card={card_name.replace(' ', '+')}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=self._config.timeout_ms)
        await page.wait_for_timeout(random.randint(500, 1500))

        html = await page.content()
        if self._parser.is_captcha(html):
            raise CaptchaDetectedError("Captcha detected on LigaMagic search page")

        card_url = self._parser.extract_card_url_from_search(html, card_name)
        if not card_url:
            card_url = await self._try_autocomplete(page, card_name)
        if not card_url:
            card_url = f"/?view=cards/card&card={quote_plus(card_name)}"

        if card_url:
            full_url = urljoin(self._base_url, card_url)
            await self._rate_limiter.wait()
            await page.goto(full_url, wait_until="domcontentloaded", timeout=self._config.timeout_ms)
            await self._wait_for_offers(page)
            if not await self._page_has_stock(page):
                logger.debug(f"No stock loaded for '{card_name}', reloading card page")
                await page.reload(wait_until="domcontentloaded", timeout=self._config.timeout_ms)
                await self._wait_for_offers(page)
            html = await page.content()

            if not self._parser.page_matches_search(html, card_name):
                logger.info(f"Wrong card page for '{card_name}', retrying from search results")
                await self._rate_limiter.wait()
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self._config.timeout_ms)
                await page.wait_for_timeout(random.randint(500, 1500))
                html = await page.content()
                retry_url = self._parser.extract_card_url_from_search(html, card_name)
                if retry_url:
                    full_url = urljoin(self._base_url, retry_url)
                    await page.goto(full_url, wait_until="domcontentloaded", timeout=self._config.timeout_ms)
                    await self._wait_for_offers(page)
                    html = await page.content()

        if self._parser.is_captcha(html):
            raise CaptchaDetectedError("Captcha detected on LigaMagic card page")

        return html

    async def _try_autocomplete(self, page: Page, card_name: str) -> str | None:
        try:
            input_el = await page.query_selector(sel.SEARCH_INPUT)
            if not input_el:
                return None

            await input_el.click()
            await input_el.fill("")
            for char in card_name:
                await input_el.type(char, delay=random.randint(30, 80))

            await page.wait_for_timeout(1500)

            items = await page.query_selector_all(sel.AUTOCOMPLETE_ITEM)
            if not items:
                return None

            best_ratio = 0
            best_item = None
            for item in items:
                href = await item.get_attribute("href") or ""
                score = self._parser.score_card_match(card_name, await item.inner_text(), href)
                if score > best_ratio:
                    best_ratio = score
                    best_item = item

            if best_item and best_ratio >= 85:
                href = await best_item.get_attribute("href")
                if href:
                    return href
                await best_item.click()
                await page.wait_for_load_state("domcontentloaded")
                return page.url

        except PlaywrightTimeout:
            logger.debug(f"Autocomplete timeout for '{card_name}'")
        except Exception as e:
            logger.debug(f"Autocomplete failed for '{card_name}': {e}")

        return None

    async def wait_for_offers(self, page: Page) -> None:
        await self._wait_for_offers(page)

    async def _wait_for_offers(self, page: Page) -> None:
        timeout_ms = min(self._config.timeout_ms, 30000)
        deadline = time.time() + timeout_ms / 1000

        while time.time() < deadline:
            try:
                ready = await page.evaluate(
                    """() => typeof cards_stock !== 'undefined'
                        && Array.isArray(cards_stock)
                        && cards_stock.length > 0"""
                )
                if ready:
                    break
            except Exception:
                pass
            await page.wait_for_timeout(500)
        else:
            try:
                await page.wait_for_selector("#marketplace-stores .store", timeout=5000)
            except PlaywrightTimeout:
                logger.debug("cards_stock not found in JS, using page content")

        try:
            await page.wait_for_function(
                "() => [...document.querySelectorAll('#marketplace-stores .new-price')]"
                ".some(el => /\\d/.test(el.innerText))",
                timeout=10000,
            )
        except PlaywrightTimeout:
            await page.wait_for_timeout(random.randint(1000, 2000))
            return
        await page.wait_for_timeout(random.randint(300, 800))

    async def _page_has_stock(self, page: Page) -> bool:
        try:
            return bool(
                await page.evaluate(
                    """() => typeof cards_stock !== 'undefined'
                        && Array.isArray(cards_stock)
                        && cards_stock.length > 0"""
                )
            )
        except Exception:
            return False

    async def paginate(self, page: Page, initial_html: str) -> AsyncIterator[str]:
        """Yield HTML for each page of offers."""
        yield initial_html
        pages_seen = 1

        while pages_seen < self._config.max_pages_per_card:
            next_btn = await page.query_selector(sel.PAGINATION_NEXT)
            if not next_btn:
                break

            try:
                if not await next_btn.is_visible():
                    break
                await self._rate_limiter.wait()
                await next_btn.click()
                await page.wait_for_load_state("domcontentloaded", timeout=self._config.timeout_ms)
                await page.wait_for_timeout(random.randint(500, 1000))
                html = await page.content()

                if self._parser.is_captcha(html):
                    raise CaptchaDetectedError("Captcha detected during pagination")

                yield html
                pages_seen += 1
            except PlaywrightTimeout:
                logger.warning(f"Pagination timeout on page {pages_seen + 1}")
                break
