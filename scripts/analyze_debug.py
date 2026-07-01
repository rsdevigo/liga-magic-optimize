import json
import re
from pathlib import Path

cache = Path(__file__).resolve().parents[1] / "data" / "cache"


def extract_js_json(html, var_name):
    marker = f"var {var_name} = "
    start = html.find(marker)
    if start == -1:
        return None
    start += len(marker)
    opener = html[start]
    if opener not in "[{":
        return None
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(html)):
        ch = html[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


for name in ["debug_search.html", "debug_card.html", "debug_lightning.html"]:
    p = cache / name
    if not p.exists():
        print("MISSING", name)
        continue
    html = p.read_text(encoding="utf-8", errors="ignore")
    print("===", name, "len", len(html))
    title = re.search(r"<title>([^<]+)</title>", html, re.I)
    if title:
        print("title:", title.group(1)[:80])
    links = re.findall(r'href="([^"]*view=cards/card[^"]*)"[^>]*>([^<]{0,100})', html, re.I)
    print("card links:", len(links))
    for href, text in links[:10]:
        print(" ", repr(text.strip()[:70]), "->", href[:100])
    stock = extract_js_json(html, "cards_stock")
    stores = extract_js_json(html, "cards_stores")
    print("cards_stock:", len(stock) if stock else None)
    print("cards_stores:", len(stores) if stores else None)
    if stock:
        print(" sample price:", stock[0].get("precoFinal"), stock[0].get("preco"))
    print()
