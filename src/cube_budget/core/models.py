"""Domain models (pure Pydantic, no I/O)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Card(BaseModel):
    id: int | None = None
    raw_name: str
    normalized_name: str
    ligamagic_id: str | None = None
    ligamagic_url: str | None = None
    color: str | None = None
    card_type: str | None = None
    mana_cost: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Store(BaseModel):
    id: int | None = None
    ligamagic_id: str
    name: str
    slug: str
    rating: float | None = None
    city: str | None = None
    state: str | None = None
    is_active: bool = True
    first_seen: datetime | None = None
    last_seen: datetime | None = None


class Offer(BaseModel):
    id: int | None = None
    card_id: int
    store_id: int
    price: float
    quantity: int = 0
    condition: str = "NM"
    language: str = "EN"
    edition: str | None = None
    is_foil: bool = False
    scraped_at: datetime | None = None
    raw_html_hash: str | None = None
    # Denormalized for reports (optional)
    card_name: str | None = None
    store_name: str | None = None


class CacheEntry(BaseModel):
    id: int | None = None
    card_id: int
    last_scraped_at: datetime
    scrape_duration_ms: int | None = None
    offers_found: int = 0
    status: str = "ok"
    error_message: str | None = None
    ttl_hours: int = 24


class AssignedCard(BaseModel):
    card: Card
    store: Store
    offer: Offer
    price: float


class MissingCardRecord(BaseModel):
    raw_name: str
    reason: str = "not_found"


class OptimizationInput(BaseModel):
    cards: list[Card]
    offers: list[Offer]
    stores: list[Store]
    min_condition: str = "NM"
    preferred_language: str = "PT"
    ignore_foil: bool = True
    min_stock: int = 1
    max_stores: int | None = None


class OptimizationResult(BaseModel):
    run_uuid: str
    assignments: list[AssignedCard] = Field(default_factory=list)
    missing: list[MissingCardRecord] = Field(default_factory=list)
    stores_used: int = 0
    total_price: float = 0.0
    solver: str = "unknown"
    duration_ms: int = 0
    total_cards: int = 0
    found_cards: int = 0
    greedy_stores: int | None = None
    greedy_price: float | None = None
    input_file: str | None = None
    created_at: datetime | None = None


class RawOffer(BaseModel):
    """Parsed offer before DB persistence."""

    store_ligamagic_id: str
    store_name: str
    store_slug: str
    price: float
    quantity: int = 0
    condition: str = "NM"
    language: str = "EN"
    edition: str | None = None
    is_foil: bool = False
    raw_html_hash: str | None = None
    store_city: str | None = None
    store_state: str | None = None
    store_rating: float | None = None


class OptimizationRunRecord(BaseModel):
    id: int | None = None
    run_uuid: str
    input_file: str | None = None
    total_cards: int | None = None
    found_cards: int | None = None
    missing_cards: int | None = None
    solver_used: str | None = None
    stores_count: int | None = None
    total_price: float | None = None
    greedy_stores: int | None = None
    greedy_price: float | None = None
    duration_ms: int | None = None
    status: str = "pending"
    created_at: datetime | None = None
    completed_at: datetime | None = None


SolverType = Literal["auto", "greedy", "ilp", "ortools"]
