"""Greedy Set Cover solver."""

from __future__ import annotations

import math

from cube_budget.optimizer.result import SolverInput, SolverOutput


class GreedySolver:
    """Greedy approximation for minimum set cover."""

    @property
    def name(self) -> str:
        return "greedy"

    def supports(self, n_vars: int) -> bool:
        return True

    def solve(self, data: SolverInput) -> SolverOutput:
        n_cards = len(data.card_ids)
        n_stores = len(data.store_ids)

        if n_cards == 0:
            return SolverOutput([], {}, 0.0, 0, self.name, optimal=True)

        uncovered = set(range(n_cards))
        selected_stores: list[int] = []
        assignments: dict[int, int] = {}

        store_coverage: dict[int, set[int]] = {}
        for j in range(n_stores):
            covered = {i for i in range(n_cards) if data.availability[i][j]}
            if covered:
                store_coverage[j] = covered

        while uncovered:
            best_store = -1
            best_ratio = -1.0

            for j, covered in store_coverage.items():
                if j in selected_stores:
                    continue
                new_coverage = covered & uncovered
                if not new_coverage:
                    continue
                ratio = len(new_coverage)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_store = j

            if best_store == -1:
                break

            selected_stores.append(best_store)
            newly_covered = store_coverage[best_store] & uncovered

            for card_idx in newly_covered:
                assignments[card_idx] = best_store

            uncovered -= newly_covered

        total_price = self._compute_price(data, assignments)
        return SolverOutput(
            selected_stores=selected_stores,
            assignments=assignments,
            total_price=total_price,
            stores_count=len(selected_stores),
            solver_name=self.name,
            optimal=False,
        )

    def solve_phase2(
        self,
        data: SolverInput,
        fixed_stores: set[int],
        max_stores: int | None = None,
    ) -> SolverOutput:
        """Assign each card to cheapest available store in fixed set."""
        assignments: dict[int, int] = {}
        used_stores: set[int] = set()

        for i in range(len(data.card_ids)):
            best_store = -1
            best_price = math.inf

            for j in fixed_stores:
                if data.availability[i][j] and data.prices[i][j] < best_price:
                    best_price = data.prices[i][j]
                    best_store = j

            if best_store >= 0:
                assignments[i] = best_store
                used_stores.add(best_store)

        if max_stores and len(used_stores) > max_stores:
            pass  # constraint violation - caller handles

        total_price = self._compute_price(data, assignments)
        return SolverOutput(
            selected_stores=list(used_stores),
            assignments=assignments,
            total_price=total_price,
            stores_count=len(used_stores),
            solver_name=self.name,
            optimal=False,
        )

    def _compute_price(self, data: SolverInput, assignments: dict[int, int]) -> float:
        total = 0.0
        for card_idx, store_idx in assignments.items():
            price = data.prices[card_idx][store_idx]
            if price < math.inf:
                total += price
        return total

    def solve_min_price(self, data: SolverInput) -> SolverOutput:
        """Assign each card to cheapest store; optionally cap store count via max_stores."""
        n_cards = len(data.card_ids)
        if n_cards == 0:
            return SolverOutput([], {}, 0.0, 0, self.name, optimal=True)

        if data.max_stores is not None:
            store_result = self.solve(data)
            if store_result.stores_count > data.max_stores:
                selected = set(store_result.selected_stores[: data.max_stores])
                return self.solve_phase2(data, selected, data.max_stores)
            return self.solve_phase2(data, set(store_result.selected_stores), data.max_stores)

        assignments: dict[int, int] = {}
        used_stores: set[int] = set()
        for i in range(n_cards):
            best_store = -1
            best_price = math.inf
            for j in range(len(data.store_ids)):
                if data.availability[i][j] and data.prices[i][j] < best_price:
                    best_price = data.prices[i][j]
                    best_store = j
            if best_store >= 0:
                assignments[i] = best_store
                used_stores.add(best_store)

        total_price = self._compute_price(data, assignments)
        return SolverOutput(
            selected_stores=list(used_stores),
            assignments=assignments,
            total_price=total_price,
            stores_count=len(used_stores),
            solver_name=f"{self.name}_price",
            optimal=False,
        )
