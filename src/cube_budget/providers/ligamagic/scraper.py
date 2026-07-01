"""LigaMagic scraper - async scraping orchestration."""

from __future__ import annotations

import asyncio
import time
from typing import Callable

from loguru import logger

from cube_budget.config.schema import AppConfig
from cube_budget.core.constants import CACHE_STATUS_ERROR, CACHE_STATUS_NOT_FOUND, CACHE_STATUS_OK
from cube_budget.core.exceptions import CaptchaDetectedError, ScraperError
from cube_budget.core.models import Card, Offer, RawOffer, Store
from cube_budget.database.repositories.offer_repo import OfferRepository
from cube_budget.database.repositories.store_repo import StoreRepository
from cube_budget.providers.browser.async_pool import AsyncBrowserPool
from cube_budget.providers.ligamagic.navigator import LigaMagicNavigator
from cube_budget.providers.ligamagic.parser import LigaMagicParser
from cube_budget.providers.ligamagic.rate_limiter import AsyncRateLimiter


class LigaMagicScraper:
    """Scrapes card offers from LigaMagic using async Playwright."""

    def __init__(
        self,
        config: AppConfig,
        store_repo: StoreRepository,
        offer_repo: OfferRepository,
        browser_pool: AsyncBrowserPool | None = None,
    ):
        self._config = config
        self._store_repo = store_repo
        self._offer_repo = offer_repo
        self._parser = LigaMagicParser()
        self._browser_pool = browser_pool or AsyncBrowserPool(config.scraper)

    async def search_card(
        self,
        card: Card,
        *,
        navigator: LigaMagicNavigator,
        db_lock: asyncio.Lock,
    ) -> tuple[list[Offer], str]:
        """
        Search for a card and return offers + cache status.
        Returns (offers, cache_status).
        """
        start = time.time()
        all_raw: list[RawOffer] = []

        try:
            async with self._browser_pool.get_page() as page:
                html = await navigator.navigate_to_card(page, card.raw_name)

                if self._parser.is_not_found(html):
                    logger.info(f"Card not found: {card.raw_name}")
                    return [], CACHE_STATUS_NOT_FOUND

                async for page_html in navigator.paginate(page, html):
                    raw_offers = self._parser.parse_offers_page(page_html)
                    all_raw.extend(raw_offers)

                if not all_raw and not self._parser.is_not_found(html):
                    logger.info(f"No offers parsed for '{card.raw_name}', retrying once")
                    await page.reload(wait_until="domcontentloaded", timeout=self._config.scraper.timeout_ms)
                    await navigator.wait_for_offers(page)
                    html = await page.content()
                    if not self._parser.is_not_found(html):
                        async for page_html in navigator.paginate(page, html):
                            raw_offers = self._parser.parse_offers_page(page_html)
                            all_raw.extend(raw_offers)

        except CaptchaDetectedError:
            logger.error(f"Captcha detected while scraping '{card.raw_name}'")
            raise
        except Exception as e:
            logger.error(f"Scrape failed for '{card.raw_name}': {e}")
            raise ScraperError(f"Failed to scrape {card.raw_name}: {e}") from e

        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            f"Scraped '{card.raw_name}': {len(all_raw)} raw offers in {duration_ms}ms"
        )

        if not all_raw:
            return [], CACHE_STATUS_NOT_FOUND

        async with db_lock:
            offers = self._persist_offers(card, all_raw)
        return offers, CACHE_STATUS_OK

    def _persist_offers(self, card: Card, raw_offers: list[RawOffer]) -> list[Offer]:
        if card.id is None:
            raise ScraperError(f"Card must have id before persisting offers: {card.raw_name}")

        self._offer_repo.delete_for_card(card.id)
        offers: list[Offer] = []

        for raw in raw_offers:
            if not self._passes_filters(raw):
                continue

            store = self._store_repo.upsert(
                Store(
                    ligamagic_id=raw.store_ligamagic_id,
                    name=raw.store_name,
                    slug=raw.store_slug,
                    rating=raw.store_rating,
                    city=raw.store_city,
                    state=raw.store_state,
                )
            )

            offer = self._offer_repo.upsert(
                Offer(
                    card_id=card.id,
                    store_id=store.id,  # type: ignore
                    price=raw.price,
                    quantity=raw.quantity,
                    condition=raw.condition,
                    language=raw.language,
                    edition=raw.edition,
                    is_foil=raw.is_foil,
                    raw_html_hash=raw.raw_html_hash,
                )
            )
            offers.append(offer)

        return offers

    def _passes_filters(self, raw: RawOffer) -> bool:
        filters = self._config.filters

        if filters.ignore_foil and raw.is_foil:
            return False

        if raw.quantity < filters.min_stock:
            return False

        from cube_budget.core.constants import CONDITION_RANK

        min_rank = CONDITION_RANK.get(filters.min_condition, 0)
        offer_rank = CONDITION_RANK.get(raw.condition, 99)
        if offer_rank > min_rank:
            return False

        if filters.preferred_language != "any":
            if raw.language != filters.preferred_language:
                return False

        return True

    def scrape_cards(
        self,
        cards: list[Card],
        on_progress: Callable[[Card, int, int], None] | None = None,
    ) -> dict[int, tuple[list[Offer], str]]:
        """Scrape multiple cards concurrently (sync entry point)."""
        return asyncio.run(self.scrape_cards_async(cards, on_progress))

    async def scrape_cards_async(
        self,
        cards: list[Card],
        on_progress: Callable[[Card, int, int], None] | None = None,
    ) -> dict[int, tuple[list[Offer], str]]:
        """
        Scrape multiple cards with controlled concurrency.

        A shared AsyncRateLimiter serializes navigations so parallel workers
        only overlap during in-page waits, keeping the same request rate as
        sequential scraping.
        """
        concurrency = self._config.scraper.concurrency
        rate_limiter = AsyncRateLimiter(self._config.scraper)
        navigator = LigaMagicNavigator(
            self._config.scraper,
            self._config.filters,
            self._parser,
            rate_limiter=rate_limiter,
        )
        semaphore = asyncio.Semaphore(concurrency)
        db_lock = asyncio.Lock()
        results: dict[int, tuple[list[Offer], str]] = {}
        progress_lock = asyncio.Lock()
        completed = 0
        total = len([c for c in cards if c.id is not None])

        logger.info(f"Scraping {total} cards with concurrency={concurrency}")

        async def scrape_one(card: Card) -> None:
            nonlocal completed
            if card.id is None:
                return

            async with semaphore:
                try:
                    offers, status = await self.search_card(
                        card, navigator=navigator, db_lock=db_lock
                    )
                    results[card.id] = (offers, status)
                except (ScraperError, CaptchaDetectedError) as e:
                    logger.error(f"Failed to scrape {card.raw_name}: {e}")
                    results[card.id] = ([], CACHE_STATUS_ERROR)

            async with progress_lock:
                completed += 1
                if on_progress:
                    on_progress(card, completed, total)

        await asyncio.gather(*(scrape_one(card) for card in cards))
        return results
