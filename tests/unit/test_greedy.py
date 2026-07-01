"""Tests for greedy solver."""

import math

from cube_budget.optimizer.matrix import MatrixBuilder
from cube_budget.optimizer.solvers.greedy import GreedySolver


class TestGreedySolver:
    def setup_method(self):
        self.solver = GreedySolver()
        self.builder = MatrixBuilder()

    def test_basic_coverage(self, sample_opt_input):
        data = self.builder.build(sample_opt_input)
        result = self.solver.solve(data)
        assert result.stores_count >= 1
        assert len(result.assignments) == 3
        assert result.total_price > 0

    def test_single_store_covers_all(self):
        from cube_budget.core.models import Card, Offer, OptimizationInput, Store

        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        stores = [Store(id=1, ligamagic_id="1", name="S1", slug="s1")]
        offers = [Offer(card_id=1, store_id=1, price=5.0, quantity=1)]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores, preferred_language="any")
        data = self.builder.build(inp)
        result = self.solver.solve(data)
        assert result.stores_count == 1
        assert result.total_price == 5.0

    def test_no_coverage(self):
        from cube_budget.core.models import Card, OptimizationInput

        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        inp = OptimizationInput(cards=cards, offers=[], stores=[])
        data = self.builder.build(inp)
        result = self.solver.solve(data)
        assert result.stores_count == 0
        assert len(result.assignments) == 0

    def test_minimize_stores_prefers_fewer(self):
        from cube_budget.core.models import Card, Offer, OptimizationInput, Store

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
            Offer(card_id=2, store_id=1, price=10.0, quantity=1),
            Offer(card_id=1, store_id=2, price=5.0, quantity=1),
            Offer(card_id=2, store_id=2, price=5.0, quantity=1),
        ]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores, preferred_language="any")
        data = self.builder.build(inp)
        result = self.solver.solve(data)
        assert result.stores_count == 1
