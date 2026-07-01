"""Optimizer result types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SolverInput:
    """Input for optimization solvers."""

    card_ids: list[int]
    card_names: list[str]
    store_ids: list[int]
    store_names: list[str]
    availability: list[list[int]]  # [card_idx][store_idx] = 0 or 1
    prices: list[list[float]]  # NaN represented as inf
    max_stores: int | None = None


@dataclass
class SolverOutput:
    """Output from optimization solvers."""

    selected_stores: list[int]  # store indices
    assignments: dict[int, int]  # card_idx -> store_idx
    total_price: float
    stores_count: int
    solver_name: str
    optimal: bool = False


@dataclass
class PhaseResult:
    """Result from a single optimization phase."""

    store_indices: set[int]
    assignments: dict[int, int]
    total_price: float
    solver: str
    optimal: bool = False
