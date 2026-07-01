"""Tests for matrix builder."""

from cube_budget.core.models import Card, Offer, OptimizationInput, Store
from cube_budget.optimizer.matrix import MatrixBuilder


class TestMatrixBuilder:
    def setup_method(self):
        self.builder = MatrixBuilder()

    def test_build_matrix(self, sample_opt_input):
        data = self.builder.build(sample_opt_input)
        assert len(data.card_ids) == 3
        assert len(data.store_ids) == 2
        assert data.availability[0][0] == 1  # Lightning Bolt at CardShop

    def test_filter_condition(self):
        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        stores = [Store(id=1, ligamagic_id="1", name="S1", slug="s1")]
        offers = [
            Offer(card_id=1, store_id=1, price=5.0, quantity=1, condition="HP"),
        ]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores, min_condition="NM")
        data = self.builder.build(inp)
        assert not any(data.availability[0])

    def test_filter_foil(self):
        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        stores = [Store(id=1, ligamagic_id="1", name="S1", slug="s1")]
        offers = [
            Offer(card_id=1, store_id=1, price=5.0, quantity=1, is_foil=True),
        ]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores, ignore_foil=True)
        data = self.builder.build(inp)
        assert not any(data.availability[0])

    def test_filter_language(self):
        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        stores = [Store(id=1, ligamagic_id="1", name="S1", slug="s1")]
        offers = [
            Offer(card_id=1, store_id=1, price=5.0, quantity=1, language="EN"),
        ]
        inp = OptimizationInput(
            cards=cards, offers=offers, stores=stores, preferred_language="PT"
        )
        data = self.builder.build(inp)
        assert not any(data.availability[0])

    def test_uncovered_cards(self, sample_opt_input):
        data = self.builder.build(sample_opt_input)
        uncovered = self.builder.get_uncovered_cards(data)
        assert uncovered == []

    def test_best_price_selected(self):
        cards = [Card(id=1, raw_name="A", normalized_name="a")]
        stores = [Store(id=1, ligamagic_id="1", name="S1", slug="s1")]
        offers = [
            Offer(card_id=1, store_id=1, price=10.0, quantity=1, condition="NM"),
            Offer(card_id=1, store_id=1, price=5.0, quantity=1, condition="NM", language="PT"),
        ]
        inp = OptimizationInput(cards=cards, offers=offers, stores=stores)
        data = self.builder.build(inp)
        assert data.prices[0][0] == 5.0
