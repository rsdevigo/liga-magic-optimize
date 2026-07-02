"""Main orchestrator - coordinates the full pipeline."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from cube_budget.cache.manager import CacheManager
from cube_budget.config.schema import AppConfig
from cube_budget.core.constants import RUN_STATUS_FAILED
from cube_budget.core.models import Card, OptimizationInput, OptimizationResult, Store
from cube_budget.database.connection import DatabaseConnection
from cube_budget.database.migrations import run_migrations
from cube_budget.database.repositories import (
    CacheRepository,
    CardRepository,
    OfferRepository,
    RunRepository,
    StoreRepository,
)
from cube_budget.optimizer.engine import OptimizerEngine
from cube_budget.providers.browser.async_pool import AsyncBrowserPool
from cube_budget.providers.ligamagic.scraper import LigaMagicScraper
from cube_budget.reports import ReportGenerator
from cube_budget.services.card_reader import CardReader
from cube_budget.services.name_normalizer import NameNormalizer


class Orchestrator:
    """Coordinates scraping, caching, optimization and reporting."""

    def __init__(self, config: AppConfig):
        self._config = config
        run_migrations(config.database.path, config.database.wal_mode, config.database.busy_timeout_ms)

        self._db = DatabaseConnection(
            config.database.path,
            wal_mode=config.database.wal_mode,
            busy_timeout_ms=config.database.busy_timeout_ms,
        )
        self._card_repo = CardRepository(self._db)
        self._store_repo = StoreRepository(self._db)
        self._offer_repo = OfferRepository(self._db)
        self._cache_repo = CacheRepository(self._db)
        self._run_repo = RunRepository(self._db)
        self._cache_manager = CacheManager(self._cache_repo, config.cache)
        self._card_reader = CardReader(NameNormalizer())
        self._optimizer = OptimizerEngine(config.optimizer)
        self._report_gen = ReportGenerator(config.output)
        self._browser_pool: AsyncBrowserPool | None = None

    def run_optimize(
        self,
        input_file: str | Path,
        fresh: bool = False,
        resume: bool = False,
        max_stores: int | None = None,
        objective: str | None = None,
        solver: str | None = None,
        output_dir: str | Path | None = None,
    ) -> OptimizationResult:
        """Run full optimization pipeline."""
        run_uuid = str(uuid.uuid4())
        input_path = str(input_file)

        if resume:
            existing = self._run_repo.get_running()
            if existing:
                run_uuid = existing.run_uuid
                run = existing
                logger.info(f"Resuming run {run_uuid}")
            else:
                run = self._run_repo.create_run(run_uuid, input_path)
        else:
            run = self._run_repo.create_run(run_uuid, input_path)

        try:
            cards = self._card_reader.read(input_file)
            logger.info(f"Loaded {len(cards)} cards from {input_file}")

            # Persist cards
            persisted: list[Card] = []
            for card in cards:
                persisted.append(self._card_repo.upsert(card))

            if fresh:
                for card in persisted:
                    if card.id:
                        self._cache_manager.invalidate(card.id)

            # Scrape stale cards
            stale = self._cache_manager.get_stale_cards(persisted)
            cached_count = len(persisted) - len(stale)
            logger.info(f"Cache: {cached_count} valid, {len(stale)} to scrape")

            if stale:
                self._scrape_cards(stale)

            if objective:
                self._config.optimizer.objective = objective  # type: ignore

            # Build optimization input
            opt_input = self._build_optimization_input(persisted, max_stores, solver)

            # Optimize
            result = self._optimizer.optimize(opt_input, run_uuid)
            result.input_file = input_path

            # Persist results
            self._run_repo.complete_run(run.id, result)  # type: ignore
            self._run_repo.save_assignments(run.id, result.assignments)  # type: ignore
            self._run_repo.save_missing(run.id, result.missing)  # type: ignore

            # Generate reports
            recent = [
                {
                    "created_at": r.created_at,
                    "total_cards": r.total_cards,
                    "stores_count": r.stores_count,
                    "total_price": r.total_price,
                    "solver_used": r.solver_used,
                }
                for r in self._run_repo.get_recent(5)
            ]
            self._report_gen.generate_all(result, output_dir, recent)

            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            self._run_repo.update_run(run.id, status=RUN_STATUS_FAILED)  # type: ignore
            raise
        finally:
            if self._browser_pool:
                asyncio.run(self._browser_pool.close())
                self._browser_pool = None

    def run_update_cache(self, input_file: str | Path | None = None) -> int:
        """Force re-scrape cards."""
        if input_file:
            cards = self._card_reader.read(input_file)
            persisted = [self._card_repo.upsert(c) for c in cards]
        else:
            persisted = self._card_repo.get_all()

        for card in persisted:
            if card.id:
                self._cache_manager.invalidate(card.id)

        self._scrape_cards(persisted)
        return len(persisted)

    def run_report(
        self,
        run_uuid: str | None = None,
        output_dir: str | Path | None = None,
    ) -> OptimizationResult | None:
        """Generate reports for an existing run."""
        if run_uuid:
            result = self._run_repo.load_result(run_uuid)
        else:
            latest = self._run_repo.get_latest()
            if not latest:
                logger.warning("No optimization runs found")
                return None
            result = self._run_repo.load_result(latest.run_uuid)

        if result:
            self._report_gen.generate_all(result, output_dir)
        return result

    def get_stats(self) -> dict:
        """Return database statistics."""
        latest = self._run_repo.get_latest()
        return {
            "cards": self._card_repo.count(),
            "stores": self._store_repo.count(),
            "offers": self._offer_repo.count(),
            "cache_entries": self._cache_manager.count_total(),
            "cache_valid": self._cache_manager.count_valid(),
            "latest_run": latest.run_uuid if latest else None,
            "latest_run_status": latest.status if latest else None,
        }

    def clean(self, cache: bool = False, all_data: bool = False) -> None:
        """Clean cache and/or all data."""
        if cache or all_data:
            self._cache_manager.invalidate_all()
            logger.info("Cache cleared")

    def _scrape_cards(self, cards: list[Card]) -> None:
        if not self._browser_pool:
            self._browser_pool = AsyncBrowserPool(self._config.scraper)

        scraper = LigaMagicScraper(
            self._config,
            self._store_repo,
            self._offer_repo,
            self._browser_pool,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scraping"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[card]}"),
        ) as progress:
            task = progress.add_task("Scraping", total=len(cards), card="")

            def on_progress(card: Card, current: int, total: int) -> None:
                progress.update(task, completed=current, card=card.raw_name)

            results = scraper.scrape_cards(cards, on_progress)

        for card in cards:
            if card.id and card.id in results:
                offers, status = results[card.id]
                self._cache_manager.mark_scraped(
                    card.id,
                    len(offers),
                    0,
                    status=status,
                )

    def _build_optimization_input(
        self,
        cards: list[Card],
        max_stores: int | None = None,
        solver: str | None = None,
    ) -> OptimizationInput:
        card_ids = [c.id for c in cards if c.id]
        offers = self._offer_repo.get_by_card_ids(card_ids)

        store_ids = list({o.store_id for o in offers})
        stores = self._store_repo.get_by_ids(store_ids)

        if solver:
            self._config.optimizer.solver = solver  # type: ignore

        effective_max = max_stores or self._config.optimizer.max_stores

        return OptimizationInput(
            cards=cards,
            offers=offers,
            stores=stores,
            min_condition=self._config.filters.min_condition,
            preferred_language=self._config.filters.preferred_language,
            ignore_foil=self._config.filters.ignore_foil,
            min_stock=self._config.filters.min_stock,
            max_stores=effective_max,
        )

    def close(self) -> None:
        if self._browser_pool:
            asyncio.run(self._browser_pool.close())
            self._browser_pool = None
        self._db.close()
