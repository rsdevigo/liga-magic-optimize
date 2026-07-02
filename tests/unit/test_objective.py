"""Tests for optimization objectives."""

import pytest

from cube_budget.config.schema import OptimizerConfig
from cube_budget.core.exceptions import InfeasibleError
from cube_budget.core.models import Card, Offer, OptimizationInput, Store
from cube_budget.optimizer.engine import OptimizerEngine
from cube_budget.optimizer.matrix import MatrixBuilder
from cube_budget.optimizer.result import SolverInput
from cube_budget.optimizer.solvers.greedy import GreedySolver
from cube_budget.optimizer.solvers.ilp_pulp import ILPSolver
from cube_budget.optimizer.solvers.ortools_cpsat import ORToolsSolver


def _price_scenario() -> OptimizationInput:
    """Two cards, two stores: cheapest per-card uses both stores."""
    cards = [
        Card(id=1, raw_name="A", normalized_name="a"),
        Card(id=2, raw_name="B", normalized_name="b"),
    ]
    stores = [
        Store(id=1, ligamagic_id="1", name="S1", slug="s1"),
        Store(id=2, ligamagic_id="2", name="S2", slug="s2"),
    ]
    offers = [
        Offer(card_id=1, store_id=1, price=10.0, quantity=1),
        Offer(card_id=1, store_id=2, price=3.0, quantity=1),
        Offer(card_id=2, store_id=1, price=5.0, quantity=1),
        Offer(card_id=2, store_id=2, price=20.0, quantity=1),
    ]
    return OptimizationInput(
        cards=cards,
        offers=offers,
        stores=stores,
        preferred_language="any",
    )


class TestPriceObjective:
    def setup_method(self):
        self.scenario = _price_scenario()
        self.builder = MatrixBuilder()

    def test_greedy_min_price_picks_cheapest_per_card(self):
        data = self.builder.build(self.scenario)
        result = GreedySolver().solve_min_price(data)
        assert result.stores_count == 2
        assert result.total_price == pytest.approx(8.0)

    def test_ilp_min_price(self):
        data = self.builder.build(self.scenario)
        result = ILPSolver(timeout_s=30).solve_min_price(data)
        assert result.total_price == pytest.approx(8.0)
        assert result.stores_count == 2

    def test_ortools_min_price(self):
        data = self.builder.build(self.scenario)
        result = ORToolsSolver(timeout_s=30).solve_min_price(data)
        assert result.total_price == pytest.approx(8.0)
        assert result.stores_count == 2

    def test_price_with_max_stores_one(self):
        inp = _price_scenario()
        inp.max_stores = 1
        data = self.builder.build(inp)
        result = ILPSolver(timeout_s=30).solve_min_price(data)
        assert result.stores_count == 1
        assert result.total_price == pytest.approx(15.0)

    def test_stores_objective_prefers_fewer_stores(self):
        data = self.builder.build(self.scenario)
        result = ILPSolver(timeout_s=30).solve(data)
        assert result.stores_count == 1
        assert result.total_price == pytest.approx(15.0)

    def test_engine_price_objective(self):
        engine = OptimizerEngine(OptimizerConfig(solver="ilp", objective="price"))
        result = engine.optimize(self.scenario, "test-uuid")
        assert result.objective == "price"
        assert result.total_price == pytest.approx(8.0)
        assert result.stores_used == 2

    def test_engine_stores_objective(self):
        engine = OptimizerEngine(OptimizerConfig(solver="ilp", objective="stores"))
        result = engine.optimize(self.scenario, "test-uuid")
        assert result.objective == "stores"
        assert result.stores_used == 1

    def test_engine_price_with_max_stores(self):
        inp = _price_scenario()
        inp.max_stores = 1
        engine = OptimizerEngine(OptimizerConfig(solver="ilp", objective="price"))
        result = engine.optimize(inp, "test-uuid")
        assert result.max_stores_limit == 1
        assert result.stores_used == 1
        assert result.total_price == pytest.approx(15.0)

    def test_price_max_stores_infeasible(self):
        """Cards split across stores with max_stores=1 is infeasible."""
        data = SolverInput(
            card_ids=[1, 2],
            card_names=["A", "B"],
            store_ids=[1, 2],
            store_names=["S1", "S2"],
            availability=[[1, 0], [0, 1]],
            prices=[[10.0, float("inf")], [float("inf"), 20.0]],
            max_stores=1,
        )
        with pytest.raises(InfeasibleError):
            ILPSolver(timeout_s=30).solve_min_price(data)
