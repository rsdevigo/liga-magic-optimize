"""Tests for cache policy."""

from datetime import datetime, timedelta

import pytest

from cube_budget.cache.manager import CacheManager
from cube_budget.cache.policy import get_ttl_hours
from cube_budget.config.schema import CacheConfig
from cube_budget.core.constants import CACHE_STATUS_ERROR, CACHE_STATUS_NOT_FOUND, CACHE_STATUS_OK
from cube_budget.core.models import CacheEntry, Card


class TestCachePolicy:
    def test_ttl_ok(self):
        config = CacheConfig()
        assert get_ttl_hours(CACHE_STATUS_OK, config) == 24

    def test_ttl_not_found(self):
        config = CacheConfig()
        assert get_ttl_hours(CACHE_STATUS_NOT_FOUND, config) == 6

    def test_ttl_error(self):
        config = CacheConfig()
        assert get_ttl_hours(CACHE_STATUS_ERROR, config) == 1


class TestCacheManager:
    def test_stale_and_valid(self, cache_repo, card_repo):
        config = CacheConfig(ttl_hours=24)
        manager = CacheManager(cache_repo, config)

        card = card_repo.upsert(Card(raw_name="Test", normalized_name="test"))
        cards = [card]

        stale = manager.get_stale_cards(cards)
        assert len(stale) == 1

        manager.mark_scraped(card.id, 5, 100, status=CACHE_STATUS_OK)  # type: ignore
        cached = manager.get_cached_cards(cards)
        assert len(cached) == 1

    def test_invalidate(self, cache_repo, card_repo):
        config = CacheConfig()
        manager = CacheManager(cache_repo, config)
        card = card_repo.upsert(Card(raw_name="A", normalized_name="a"))
        manager.mark_scraped(card.id, 3, 50)  # type: ignore
        assert manager.is_valid(card.id)  # type: ignore
        manager.invalidate(card.id)  # type: ignore
        assert not manager.is_valid(card.id)  # type: ignore

    def test_invalidate_all(self, cache_repo, card_repo):
        config = CacheConfig()
        manager = CacheManager(cache_repo, config)
        c1 = card_repo.upsert(Card(raw_name="A", normalized_name="a"))
        c2 = card_repo.upsert(Card(raw_name="B", normalized_name="b"))
        manager.mark_scraped(c1.id, 3, 50)  # type: ignore
        manager.mark_scraped(c2.id, 1, 30)  # type: ignore
        manager.invalidate_all()
        assert manager.count_total() == 0
