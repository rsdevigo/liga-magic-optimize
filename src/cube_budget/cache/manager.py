"""Cache manager - hit/miss/invalidation logic."""

from __future__ import annotations

from datetime import datetime

from cube_budget.cache.policy import get_ttl_hours
from cube_budget.config.schema import CacheConfig
from cube_budget.core.constants import CACHE_STATUS_OK
from cube_budget.core.models import CacheEntry, Card
from cube_budget.database.repositories.cache_repo import CacheRepository


class CacheManager:
    """Manages cache validity and invalidation."""

    def __init__(self, cache_repo: CacheRepository, config: CacheConfig):
        self._repo = cache_repo
        self._config = config

    def is_valid(self, card_id: int) -> bool:
        return self._repo.is_valid(card_id)

    def mark_scraped(
        self,
        card_id: int,
        offers_count: int,
        duration_ms: int,
        status: str = CACHE_STATUS_OK,
        error_message: str | None = None,
    ) -> CacheEntry:
        ttl = get_ttl_hours(status, self._config)
        entry = CacheEntry(
            card_id=card_id,
            last_scraped_at=datetime.now(),
            scrape_duration_ms=duration_ms,
            offers_found=offers_count,
            status=status,
            error_message=error_message,
            ttl_hours=ttl,
        )
        return self._repo.upsert(entry)

    def invalidate(self, card_id: int) -> None:
        self._repo.invalidate(card_id)

    def invalidate_all(self) -> None:
        self._repo.invalidate_all()

    def get_stale_cards(self, cards: list[Card]) -> list[Card]:
        """Return cards that need to be scraped."""
        stale = []
        for card in cards:
            if card.id is None or not self.is_valid(card.id):
                stale.append(card)
        return stale

    def get_cached_cards(self, cards: list[Card]) -> list[Card]:
        """Return cards with valid cache."""
        return [c for c in cards if c.id is not None and self.is_valid(c.id)]

    def count_valid(self) -> int:
        return self._repo.count_valid()

    def count_total(self) -> int:
        return self._repo.count()
