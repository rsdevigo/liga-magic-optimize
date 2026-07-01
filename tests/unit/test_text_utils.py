"""Tests for text utilities."""

from cube_budget.utils.text import normalize_text, parse_price, slugify


class TestTextUtils:
    def test_parse_price_brazilian(self):
        assert parse_price("R$ 12,50") == 12.50
        assert parse_price("R$1.234,56") == 1234.56
        assert parse_price("6.60") == 6.60

    def test_parse_price_invalid(self):
        assert parse_price("") is None
        assert parse_price("abc") is None

    def test_slugify(self):
        assert slugify("Card Shop SP") == "card-shop-sp"

    def test_normalize_text(self):
        assert normalize_text("  Hello   World  ") == "hello world"
