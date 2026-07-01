"""ILP solver using PuLP + CBC."""

from __future__ import annotations

import math

import pulp

from cube_budget.core.exceptions import InfeasibleError, OptimizerError
from cube_budget.optimizer.result import SolverInput, SolverOutput


class ILPSolver:
    """Integer Linear Programming solver for set cover."""

    def __init__(self, timeout_s: int = 120):
        self._timeout = timeout_s

    @property
    def name(self) -> str:
        return "ilp_pulp"

    def supports(self, n_vars: int) -> bool:
        return n_vars <= 15000

    def solve(self, data: SolverInput) -> SolverOutput:
        n_cards = len(data.card_ids)
        n_stores = len(data.store_ids)

        if n_cards == 0:
            return SolverOutput([], {}, 0.0, 0, self.name, optimal=True)

        prob = pulp.LpProblem("CubeBudget", pulp.LpMinimize)

        y = {j: pulp.LpVariable(f"y_{j}", cat="Binary") for j in range(n_stores)}
        x = {
            (i, j): pulp.LpVariable(f"x_{i}_{j}", cat="Binary")
            for i in range(n_cards)
            for j in range(n_stores)
            if data.availability[i][j]
        }

        # Phase 1: minimize number of stores
        prob += pulp.lpSum(y[j] for j in range(n_stores))

        for i in range(n_cards):
            available = [j for j in range(n_stores) if data.availability[i][j]]
            if not available:
                continue
            prob += pulp.lpSum(x[(i, j)] for j in available) >= 1

        for (i, j) in x:
            prob += x[(i, j)] <= y[j]

        if data.max_stores:
            prob += pulp.lpSum(y[j] for j in range(n_stores)) <= data.max_stores

        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self._timeout)
        status = prob.solve(solver)

        if pulp.LpStatus[status] not in ("Optimal", "Not Solved"):
            raise InfeasibleError("No feasible solution found")

        k_star = sum(int(pulp.value(y[j]) or 0) for j in range(n_stores))

        # Phase 2: minimize price with fixed k*
        return self._solve_phase2(data, k_star, x, y, n_cards, n_stores)

    def _solve_phase2(
        self,
        data: SolverInput,
        k_star: int,
        x_vars: dict,
        y_vars: dict,
        n_cards: int,
        n_stores: int,
    ) -> SolverOutput:
        prob2 = pulp.LpProblem("CubeBudget_Phase2", pulp.LpMinimize)

        y = {j: pulp.LpVariable(f"y2_{j}", cat="Binary") for j in range(n_stores)}
        x = {
            (i, j): pulp.LpVariable(f"x2_{i}_{j}", cat="Binary")
            for i in range(n_cards)
            for j in range(n_stores)
            if data.availability[i][j]
        }

        prob2 += pulp.lpSum(
            data.prices[i][j] * x[(i, j)] for (i, j) in x
        )

        prob2 += pulp.lpSum(y[j] for j in range(n_stores)) <= k_star

        for i in range(n_cards):
            available = [j for j in range(n_stores) if data.availability[i][j]]
            if not available:
                continue
            prob2 += pulp.lpSum(x[(i, j)] for j in available) == 1

        for (i, j) in x:
            prob2 += x[(i, j)] <= y[j]

        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self._timeout)
        status = prob2.solve(solver)

        if pulp.LpStatus[status] not in ("Optimal", "Not Solved"):
            raise OptimizerError("Phase 2 optimization failed")

        selected_stores = [j for j in range(n_stores) if int(pulp.value(y[j]) or 0)]
        assignments = {}
        for i in range(n_cards):
            for j in range(n_stores):
                if (i, j) in x and int(pulp.value(x[(i, j)]) or 0):
                    assignments[i] = j
                    break

        total_price = sum(
            data.prices[i][j] for i, j in assignments.items()
        )

        return SolverOutput(
            selected_stores=selected_stores,
            assignments=assignments,
            total_price=total_price,
            stores_count=len(selected_stores),
            solver_name=self.name,
            optimal=pulp.LpStatus[status] == "Optimal",
        )
