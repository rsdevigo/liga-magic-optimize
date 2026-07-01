from pathlib import Path

from cube_budget.providers.ligamagic.parser import LigaMagicParser


class TestCardMatch:
    def setup_method(self):
        self.parser = LigaMagicParser()

    def test_score_prefers_exact_name_over_double_faced(self):
        assert self.parser.score_card_match("Lightning Bolt", "Lightning Bolt") == 100
        assert self.parser.score_card_match(
            "Lightning Bolt", "Emeritus of Conflict // Lightning Bolt"
        ) == 80

    def test_extract_card_url_from_search_fixture(self):
        html = Path(__file__).parent.parent / "fixtures" / "sample_html" / "search_results.html"
        if not html.exists():
            debug = (
                Path(__file__).parent.parent.parent
                / "data"
                / "cache"
                / "debug_search.html"
            )
            html = debug
        content = html.read_text(encoding="utf-8")
        url = self.parser.extract_card_url_from_search(content, "Lightning Bolt")
        assert url is not None
        assert "Lightning+Bolt" in url.replace(" ", "+")
        assert "Emeritus" not in url
