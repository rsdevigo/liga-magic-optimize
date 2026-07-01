"""Global pytest fixtures."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cube_budget.config.schema import AppConfig, CacheConfig, DatabaseConfig, OptimizerConfig
from cube_budget.core.models import Card, Offer, OptimizationInput, Store
from cube_budget.database.connection import DatabaseConnection
from cube_budget.database.migrations import run_migrations
from cube_budget.database.repositories import (
    CacheRepository,
    CardRepository,
    OfferRepository,
    RunRepository,
    StoreRepository,
)


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite"


@pytest.fixture
def db_connection(tmp_db_path: Path) -> DatabaseConnection:
    run_migrations(str(tmp_db_path))
    return DatabaseConnection(str(tmp_db_path))


@pytest.fixture
def card_repo(db_connection: DatabaseConnection) -> CardRepository:
    return CardRepository(db_connection)


@pytest.fixture
def store_repo(db_connection: DatabaseConnection) -> StoreRepository:
    return StoreRepository(db_connection)


@pytest.fixture
def offer_repo(db_connection: DatabaseConnection) -> OfferRepository:
    return OfferRepository(db_connection)


@pytest.fixture
def cache_repo(db_connection: DatabaseConnection) -> CacheRepository:
    return CacheRepository(db_connection)


@pytest.fixture
def run_repo(db_connection: DatabaseConnection) -> RunRepository:
    return RunRepository(db_connection)


@pytest.fixture
def sample_cards() -> list[Card]:
    return [
        Card(id=1, raw_name="Lightning Bolt", normalized_name="lightning bolt"),
        Card(id=2, raw_name="Counterspell", normalized_name="counterspell"),
        Card(id=3, raw_name="Brainstorm", normalized_name="brainstorm"),
    ]


@pytest.fixture
def sample_stores() -> list[Store]:
    return [
        Store(id=1, ligamagic_id="101", name="CardShop SP", slug="cardshop-sp"),
        Store(id=2, ligamagic_id="102", name="Magic Rio", slug="magic-rio"),
    ]


@pytest.fixture
def sample_offers() -> list[Offer]:
    return [
        Offer(id=1, card_id=1, store_id=1, price=12.50, quantity=4, condition="NM", language="PT"),
        Offer(id=2, card_id=1, store_id=2, price=15.00, quantity=2, condition="SP", language="EN"),
        Offer(id=3, card_id=2, store_id=1, price=5.00, quantity=3, condition="NM", language="PT"),
        Offer(id=4, card_id=2, store_id=2, price=4.50, quantity=1, condition="NM", language="PT"),
        Offer(id=5, card_id=3, store_id=2, price=8.00, quantity=2, condition="NM", language="PT"),
    ]


@pytest.fixture
def sample_opt_input(sample_cards, sample_stores, sample_offers) -> OptimizationInput:
    return OptimizationInput(
        cards=sample_cards,
        offers=sample_offers,
        stores=sample_stores,
        min_condition="NM",
        preferred_language="PT",
        ignore_foil=True,
        min_stock=1,
    )


@pytest.fixture
def app_config(tmp_db_path: Path, tmp_path: Path) -> AppConfig:
    return AppConfig(
        cache=CacheConfig(ttl_hours=24),
        optimizer=OptimizerConfig(solver="greedy"),
        database=DatabaseConfig(path=str(tmp_db_path)),
    )
