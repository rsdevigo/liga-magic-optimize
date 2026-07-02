"""OR-Tools CP-SAT solver."""

from __future__ import annotations

import math

from ortools.sat.python import cp_model

from cube_budget.core.exceptions import InfeasibleError, OptimizerError
from cube_budget.optimizer.result import SolverInput, SolverOutput


class ORToolsSolver:
    """Google OR-Tools CP-SAT solver."""

    def __init__(self, timeout_s: int = 300):
        self._timeout = timeout_s

    @property
    def name(self) -> str:
        return "ortools_cpsat"

    def supports(self, n_vars: int) -> bool:
        return True

    def solve(self, data: SolverInput) -> SolverOutput:
        n_cards = len(data.card_ids)
        n_stores = len(data.store_ids)

        if n_cards == 0:
            return SolverOutput([], {}, 0.0, 0, self.name, optimal=True)

        # Phase 1: minimize stores
        k_star = self._minimize_stores(data, n_cards, n_stores)

        # Phase 2: minimize price
        return self._minimize_price(data, n_cards, n_stores, k_star)

    def _minimize_stores(self, data: SolverInput, n_cards: int, n_stores: int) -> int:
        model = cp_model.CpModel()

        y = [model.new_bool_var(f"y_{j}") for j in range(n_stores)]
        x = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if data.availability[i][j]:
                    x[(i, j)] = model.new_bool_var(f"x_{i}_{j}")

        model.minimize(sum(y))

        for i in range(n_cards):
            available = [j for j in range(n_stores) if data.availability[i][j]]
            if available:
                model.add(sum(x[(i, j)] for j in available) >= 1)

        for (i, j) in x:
            model.add(x[(i, j)] <= y[j])

        if data.max_stores:
            model.add(sum(y) <= data.max_stores)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self._timeout)
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InfeasibleError("OR-Tools: no feasible solution for store minimization")

        return sum(solver.value(y[j]) for j in range(n_stores))

    def _minimize_price(
        self, data: SolverInput, n_cards: int, n_stores: int, k_star: int
    ) -> SolverOutput:
        model = cp_model.CpModel()

        y = [model.new_bool_var(f"y2_{j}") for j in range(n_stores)]
        x = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if data.availability[i][j]:
                    x[(i, j)] = model.new_bool_var(f"x2_{i}_{j}")

        # Scale prices to integers (cents)
        scale = 100
        objective_terms = []
        for (i, j) in x:
            price_cents = int(data.prices[i][j] * scale)
            objective_terms.append(price_cents * x[(i, j)])

        model.minimize(sum(objective_terms))
        model.add(sum(y) <= k_star)

        for i in range(n_cards):
            available = [j for j in range(n_stores) if data.availability[i][j]]
            if available:
                model.add(sum(x[(i, j)] for j in available) == 1)

        for (i, j) in x:
            model.add(x[(i, j)] <= y[j])

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self._timeout)
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise OptimizerError("OR-Tools: phase 2 price minimization failed")

        selected_stores = [j for j in range(n_stores) if solver.value(y[j])]
        assignments = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if (i, j) in x and solver.value(x[(i, j)]):
                    assignments[i] = j
                    break

        total_price = sum(data.prices[i][j] for i, j in assignments.items())

        return SolverOutput(
            selected_stores=selected_stores,
            assignments=assignments,
            total_price=total_price,
            stores_count=len(selected_stores),
            solver_name=self.name,
            optimal=status == cp_model.OPTIMAL,
        )

    def solve_min_price(self, data: SolverInput) -> SolverOutput:
        """Minimize total price subject to max_stores if set."""
        n_cards = len(data.card_ids)
        n_stores = len(data.store_ids)

        if n_cards == 0:
            return SolverOutput([], {}, 0.0, 0, self.name, optimal=True)

        model = cp_model.CpModel()

        y = [model.new_bool_var(f"y_{j}") for j in range(n_stores)]
        x = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if data.availability[i][j]:
                    x[(i, j)] = model.new_bool_var(f"x_{i}_{j}")

        scale = 100
        objective_terms = []
        for (i, j) in x:
            price_cents = int(data.prices[i][j] * scale)
            objective_terms.append(price_cents * x[(i, j)])

        model.minimize(sum(objective_terms))

        for i in range(n_cards):
            available = [j for j in range(n_stores) if data.availability[i][j]]
            if available:
                model.add(sum(x[(i, j)] for j in available) == 1)

        for (i, j) in x:
            model.add(x[(i, j)] <= y[j])

        if data.max_stores:
            model.add(sum(y) <= data.max_stores)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self._timeout)
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InfeasibleError("OR-Tools: no feasible solution for price minimization")

        selected_stores = [j for j in range(n_stores) if solver.value(y[j])]
        assignments = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if (i, j) in x and solver.value(x[(i, j)]):
                    assignments[i] = j
                    break

        total_price = sum(data.prices[i][j] for i, j in assignments.items())

        return SolverOutput(
            selected_stores=selected_stores,
            assignments=assignments,
            total_price=total_price,
            stores_count=len(selected_stores),
            solver_name=f"{self.name}_price",
            optimal=status == cp_model.OPTIMAL,
        )
