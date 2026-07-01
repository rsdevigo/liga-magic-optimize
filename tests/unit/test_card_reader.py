"""Tests for card reader."""

from pathlib import Path

import pytest

from cube_budget.core.exceptions import CardReadError
from cube_budget.services.card_reader import CardReader


class TestCardReader:
    def test_read_valid_file(self, tmp_path: Path):
        f = tmp_path / "cube.txt"
        f.write_text("Lightning Bolt\nCounterspell\n# comment\n\nBrainstorm\n", encoding="utf-8")
        reader = CardReader()
        cards = reader.read(f)
        assert len(cards) == 3
        assert cards[0].raw_name == "Lightning Bolt"

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        reader = CardReader()
        with pytest.raises(CardReadError):
            reader.read(f)

    def test_file_not_found(self):
        reader = CardReader()
        with pytest.raises(CardReadError):
            reader.read("/nonexistent/file.txt")

    def test_comments_only(self, tmp_path: Path):
        f = tmp_path / "comments.txt"
        f.write_text("# only comments\n# another\n", encoding="utf-8")
        reader = CardReader()
        with pytest.raises(CardReadError):
            reader.read(f)

    def test_sample_fixture(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "sample_cube.txt"
        reader = CardReader()
        cards = reader.read(fixture)
        assert len(cards) == 30
