"""Integration tests for HTML parser."""

from pathlib import Path

from cube_budget.providers.ligamagic.parser import LigaMagicParser


class TestScraperMock:
    def setup_method(self):
        self.parser = LigaMagicParser()
        self.fixture_dir = Path(__file__).parent.parent / "fixtures" / "sample_html"

    def test_parse_offers_from_fixture(self):
        html = (self.fixture_dir / "card_page.html").read_text(encoding="utf-8")
        offers = self.parser.parse_offers_page(html)
        assert len(offers) == 3
        assert offers[0].store_name == "CardShop SP"
        assert offers[0].price == 12.50
        assert offers[0].condition == "NM"
        assert offers[0].language == "PT"

    def test_parse_prices(self):
        html = (self.fixture_dir / "card_page.html").read_text(encoding="utf-8")
        offers = self.parser.parse_offers_page(html)
        prices = [o.price for o in offers]
        assert 10.0 in prices
        assert 12.50 in prices
        assert 15.0 in prices

    def test_not_found_detection(self):
        html = "<html><body><div class='not-found'>Nenhum resultado</div></body></html>"
        assert self.parser.is_not_found(html)

    def test_captcha_detection(self):
        html = '<html><body><iframe src="https://captcha.example.com"></iframe></body></html>'
        assert self.parser.is_captcha(html)

    def test_parse_js_embedded_offers(self):
        html = """
        <html><body>
        <script>
        var cards_stock = [{"id":1,"idEdicao":"230","preco":"6.60","precoFinal":"5.94","qualid":"2","idioma":"8","extras":0,"lj_id":101,"quantFilter":4}];
        var cards_stores = {"101":{"lj_name":"CardShop SP","lj_cidade":"São Paulo","lj_uf":"SP","lj_ref":"5"}};
        var cards_editions = [{"id":230,"name":"Magic 2011","code":"m11"}];
        var dataQuality = [{"id":2,"acron":"NM"}];
        var dataLanguage = [{"id":8,"acron":"PT"}];
        </script>
        </body></html>
        """
        offers = self.parser.parse_offers_page(html)
        assert len(offers) == 1
        assert offers[0].store_name == "CardShop SP"
        assert offers[0].price == 5.94
        assert offers[0].condition == "NM"
        assert offers[0].language == "PT"
        assert offers[0].quantity == 4
