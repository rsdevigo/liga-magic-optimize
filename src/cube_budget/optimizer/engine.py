"""Optimizer engine - selects and orchestrates solvers."""

from __future__ import annotations

import time

from loguru import logger

from cube_budget.config.schema import OptimizerConfig
from cube_budget.core.constants import (
    OBJECTIVE_PRICE,
    OBJECTIVE_STORES,
    SOLVER_AUTO,
    SOLVER_GREEDY,
    SOLVER_ILP,
    SOLVER_ORTOOLS,
)
from cube_budget.core.exceptions import InfeasibleError, OptimizerError
from cube_budget.core.models import (
    AssignedCard,
    Card,
    MissingCardRecord,
    Offer,
    OptimizationInput,
    OptimizationResult,
    Store,
)
from cube_budget.optimizer.matrix import MatrixBuilder
from cube_budget.optimizer.result import SolverInput, SolverOutput
from cube_budget.optimizer.solvers.greedy import GreedySolver
from cube_budget.optimizer.solvers.ilp_pulp import ILPSolver
from cube_budget.optimizer.solvers.ortools_cpsat import ORToolsSolver


class OptimizerEngine:
    """Hybrid optimization pipeline with configurable objective."""

    def __init__(self, config: OptimizerConfig):
        self._config = config
        self._matrix_builder = MatrixBuilder()
        self._greedy = GreedySolver()
        self._ilp = ILPSolver(timeout_s=config.ilp_timeout_s)
        self._ortools = ORToolsSolver(timeout_s=config.ortools_timeout_s)

    def optimize(
        self,
        opt_input: OptimizationInput,
        run_uuid: str,
    ) -> OptimizationResult:
        start = time.time()

        solver_data = self._matrix_builder.build(opt_input)
        uncovered = self._matrix_builder.get_uncovered_cards(solver_data)

        n_vars = len(solver_data.card_ids) * len(solver_data.store_ids)
        objective = self._config.objective
        logger.info(
            f"Optimizing {len(solver_data.card_ids)} cards x "
            f"{len(solver_data.store_ids)} stores ({n_vars} vars), objective={objective}"
        )

        greedy_result = self._greedy.solve(solver_data)
        logger.info(
            f"Greedy: {greedy_result.stores_count} stores, "
            f"R$ {greedy_result.total_price:.2f}"
        )

        if objective == OBJECTIVE_PRICE:
            solver_output = self._select_and_solve_price(solver_data, n_vars, greedy_result)
        else:
            solver_output = self._select_and_solve_stores(solver_data, n_vars, greedy_result)

        result = self._build_result(
            opt_input,
            solver_data,
            solver_output,
            uncovered,
            run_uuid,
            greedy_result,
            int((time.time() - start) * 1000),
            objective=objective,
        )

        return result

    def _select_and_solve_stores(
        self,
        data: SolverInput,
        n_vars: int,
        greedy_result: SolverOutput,
    ) -> SolverOutput:
        solver_choice = self._config.solver

        if solver_choice == SOLVER_GREEDY:
            return greedy_result

        if solver_choice == SOLVER_ILP:
            try:
                return self._ilp.solve(data)
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"ILP failed: {e}. Using greedy fallback.")
                return greedy_result

        if solver_choice == SOLVER_ORTOOLS:
            try:
                return self._ortools.solve(data)
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"OR-Tools failed: {e}. Using greedy fallback.")
                return greedy_result

        if n_vars < self._config.ilp_ortools_threshold:
            try:
                result = self._ilp.solve(data)
                if result.stores_count <= greedy_result.stores_count:
                    return result
                logger.info("ILP found more stores than greedy, trying OR-Tools")
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"ILP failed: {e}")

        try:
            result = self._ortools.solve(data)
            if result.stores_count <= greedy_result.stores_count:
                return result
        except (InfeasibleError, OptimizerError) as e:
            logger.warning(f"OR-Tools failed: {e}")

        return greedy_result

    def _select_and_solve_price(
        self,
        data: SolverInput,
        n_vars: int,
        greedy_result: SolverOutput,
    ) -> SolverOutput:
        solver_choice = self._config.solver
        price_greedy = self._greedy.solve_min_price(data)

        if solver_choice == SOLVER_GREEDY:
            return price_greedy

        if solver_choice == SOLVER_ILP:
            try:
                return self._ilp.solve_min_price(data)
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"ILP price failed: {e}. Using greedy fallback.")
                return price_greedy

        if solver_choice == SOLVER_ORTOOLS:
            try:
                return self._ortools.solve_min_price(data)
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"OR-Tools price failed: {e}. Using greedy fallback.")
                return price_greedy

        if n_vars < self._config.ilp_ortools_threshold:
            try:
                return self._ilp.solve_min_price(data)
            except (InfeasibleError, OptimizerError) as e:
                logger.warning(f"ILP price failed: {e}")

        try:
            return self._ortools.solve_min_price(data)
        except (InfeasibleError, OptimizerError) as e:
            logger.warning(f"OR-Tools price failed: {e}")

        return price_greedy

    def _build_result(
        self,
        opt_input: OptimizationInput,
        solver_data: SolverInput,
        output: SolverOutput,
        uncovered: list[str],
        run_uuid: str,
        greedy_result: SolverOutput,
        duration_ms: int,
        objective: str = OBJECTIVE_STORES,
    ) -> OptimizationResult:
        card_map = {c.id: c for c in opt_input.cards if c.id}
        store_map = {s.id: s for s in opt_input.stores if s.id}

        offer_lookup: dict[tuple[int, int], Offer] = {}
        for offer in opt_input.offers:
            key = (offer.card_id, offer.store_id)
            if key not in offer_lookup or offer.price < offer_lookup[key].price:
                offer_lookup[key] = offer

        assignments: list[AssignedCard] = []
        for card_idx, store_idx in output.assignments.items():
            card_id = solver_data.card_ids[card_idx]
            store_id = solver_data.store_ids[store_idx]

            card = card_map.get(card_id)
            store = store_map.get(store_id)
            offer = offer_lookup.get((card_id, store_id))

            if card and store and offer:
                assignments.append(
                    AssignedCard(
                        card=card,
                        store=store,
                        offer=offer,
                        price=offer.price,
                    )
                )

        missing = [MissingCardRecord(raw_name=name, reason="not_found") for name in uncovered]

        return OptimizationResult(
            run_uuid=run_uuid,
            assignments=assignments,
            missing=missing,
            stores_used=output.stores_count,
            total_price=output.total_price,
            solver=output.solver_name,
            objective=objective,
            max_stores_limit=opt_input.max_stores,
            duration_ms=duration_ms,
            total_cards=len(opt_input.cards),
            found_cards=len(assignments),
            greedy_stores=greedy_result.stores_count,
            greedy_price=greedy_result.total_price,
        )
