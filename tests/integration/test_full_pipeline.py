"""End-to-end pipeline test with mock data."""

import uuid

from cube_budget.core.models import Card, Offer, OptimizationInput, Store
from cube_budget.optimizer.engine import OptimizerEngine
from cube_budget.config.schema import OptimizerConfig


class TestFullPipeline:
    def test_optimize_with_mock_data(self, sample_opt_input):
        engine = OptimizerEngine(OptimizerConfig(solver="greedy"))
        result = engine.optimize(sample_opt_input, str(uuid.uuid4()))

        assert result.found_cards == 3
        assert result.stores_used >= 1
        assert result.total_price > 0
        assert result.solver == "greedy"

    def test_optimize_ilp(self, sample_opt_input):
        engine = OptimizerEngine(OptimizerConfig(solver="ilp"))
        result = engine.optimize(sample_opt_input, str(uuid.uuid4()))
        assert result.found_cards == 3

    def test_all_cards_missing(self):
        cards = [
            Card(id=1, raw_name="Unknown", normalized_name="unknown"),
        ]
        inp = OptimizationInput(cards=cards, offers=[], stores=[])
        engine = OptimizerEngine(OptimizerConfig(solver="greedy"))
        result = engine.optimize(inp, str(uuid.uuid4()))
        assert result.found_cards == 0
        assert len(result.missing) == 1

    def test_single_card_multiple_stores(self):
        cards = [Card(id=1, raw_name="Bolt", normalized_name="bolt")]
        stores = [
            Store(id=1, ligamagic_id="1", name="Cheap", slug="cheap"),
            Store(id=2, ligamagic_id="2", name="Expensive", slug="expensive"),
        ]
        offers = [
            Offer(card_id=1, store_id=1, price=5.0, quantity=1),
            Offer(card_id=1, store_id=2, price=20.0, quantity=1),
        ]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores, preferred_language="any")
        engine = OptimizerEngine(OptimizerConfig(solver="ilp"))
        result = engine.optimize(inp, str(uuid.uuid4()))
        assert result.stores_used == 1
        assert result.total_price == 5.0

    def test_price_objective_pipeline(self):
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
        inp = OptimizationInput(
            cards=cards, offers=offers, stores=stores, preferred_language="any"
        )
        engine = OptimizerEngine(OptimizerConfig(solver="ilp", objective="price"))
        result = engine.optimize(inp, str(uuid.uuid4()))
        assert result.objective == "price"
        assert result.total_price == 8.0
        assert result.stores_used == 2
