import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cube_budget.providers.ligamagic.parser import LigaMagicParser

cache = Path(__file__).resolve().parents[1] / "data" / "cache"
parser = LigaMagicParser()

for name in ["debug_card.html", "debug_lightning.html"]:
    p = cache / name
    html = p.read_text(encoding="utf-8", errors="ignore")
    offers = parser.parse_offers_page(html)
    print(name, "offers:", len(offers))
    if offers:
        for o in offers[:3]:
            print(f"  {o.store_name} R${o.price} {o.condition} {o.language} foil={o.is_foil}")

html = (cache / "debug_search.html").read_text(encoding="utf-8", errors="ignore")
for card in ["Lightning Bolt", "Counterspell", "Brainstorm"]:
    url = parser.extract_card_url_from_search(html, card)
    print(f"search match {card!r}:", url)
