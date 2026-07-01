"""Tests for orchestrator with mocked scraper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cube_budget.config.schema import AppConfig, DatabaseConfig, OptimizerConfig, OutputConfig
from cube_budget.core.models import Card, Offer, Store
from cube_budget.database.repositories import CardRepository, OfferRepository, StoreRepository
from cube_budget.services.orchestrator import Orchestrator


@pytest.fixture
def orch_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        database=DatabaseConfig(path=str(tmp_path / "orch.sqlite")),
        optimizer=OptimizerConfig(solver="greedy"),
        output=OutputConfig(reports_dir=str(tmp_path / "reports")),
    )


class TestOrchestrator:
    @patch("cube_budget.services.orchestrator.LigaMagicScraper")
    def test_optimize_with_cached_data(self, mock_scraper_cls, orch_config, tmp_path: Path):
        # Pre-populate database
        from cube_budget.database.connection import DatabaseConnection
        from cube_budget.database.migrations import run_migrations

        run_migrations(orch_config.database.path)
        db = DatabaseConnection(orch_config.database.path)
        card_repo = CardRepository(db)
        store_repo = StoreRepository(db)
        offer_repo = OfferRepository(db)

        card = card_repo.upsert(Card(raw_name="Lightning Bolt", normalized_name="lightning bolt"))
        store = store_repo.upsert(Store(ligamagic_id="1", name="Shop", slug="shop"))
        offer_repo.upsert(
            Offer(
                card_id=card.id,  # type: ignore
                store_id=store.id,  # type: ignore
                price=10.0,
                quantity=1,
                language="PT",
            )
        )

        # Mark cache valid
        from cube_budget.cache.manager import CacheManager
        from cube_budget.database.repositories import CacheRepository
        from cube_budget.config.schema import CacheConfig

        cache_mgr = CacheManager(CacheRepository(db), CacheConfig())
        cache_mgr.mark_scraped(card.id, 1, 100)  # type: ignore

        db.close()

        input_file = tmp_path / "cube.txt"
        input_file.write_text("Lightning Bolt\n", encoding="utf-8")

        orch = Orchestrator(orch_config)
        try:
            result = orch.run_optimize(input_file, fresh=False)
            assert result.found_cards == 1
            assert result.stores_used == 1
            mock_scraper_cls.return_value.scrape_cards.assert_not_called()
        finally:
            orch.close()

    def test_get_stats(self, orch_config):
        orch = Orchestrator(orch_config)
        try:
            stats = orch.get_stats()
            assert "cards" in stats
            assert "stores" in stats
        finally:
            orch.close()

    def test_clean_cache(self, orch_config):
        orch = Orchestrator(orch_config)
        try:
            orch.clean(cache=True)
        finally:
            orch.close()
