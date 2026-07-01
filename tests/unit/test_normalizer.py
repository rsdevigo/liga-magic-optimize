"""Tests for name normalizer."""

from cube_budget.services.name_normalizer import NameNormalizer


class TestNameNormalizer:
    def setup_method(self):
        self.normalizer = NameNormalizer()

    def test_basic_normalization(self):
        assert self.normalizer.normalize("Lightning Bolt") == "lightning bolt"

    def test_extra_spaces(self):
        assert self.normalizer.normalize("  Lightning   Bolt  ") == "lightning bolt"

    def test_accents(self):
        assert self.normalizer.normalize("São Tomé") == "sao tome"

    def test_apostrophe(self):
        result = self.normalizer.normalize("Teferi's Protection")
        assert "teferi" in result

    def test_deduplication(self):
        cards = self.normalizer.normalize_batch(["Lightning Bolt", "lightning bolt", "LIGHTNING BOLT"])
        assert len(cards) == 1

    def test_to_card(self):
        card = self.normalizer.to_card("Counterspell")
        assert card.raw_name == "Counterspell"
        assert card.normalized_name == "counterspell"
