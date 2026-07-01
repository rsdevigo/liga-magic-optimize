"""Parse LigaMagic HTML into RawOffer objects."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from bs4 import BeautifulSoup, Tag
from loguru import logger

from cube_budget.core.models import RawOffer
from cube_budget.providers.ligamagic import selectors as sel
from cube_budget.utils.text import normalize_text, parse_price, slugify


class LigaMagicParser:
    """Extract offer data from HTML pages."""

    CONDITION_MAP = {
        "nm": "NM",
        "near mint": "NM",
        "sp": "SP",
        "slightly played": "SP",
        "mp": "MP",
        "moderately played": "MP",
        "hp": "HP",
        "heavily played": "HP",
        "dmg": "DMG",
        "damaged": "DMG",
    }

    LANGUAGE_MAP = {
        "portugues": "PT",
        "português": "PT",
        "pt": "PT",
        "ingles": "EN",
        "inglês": "EN",
        "en": "EN",
        "espanhol": "ES",
        "es": "ES",
        "japones": "JP",
        "japonês": "JP",
        "jp": "JP",
    }

    QUALITY_ACRON_MAP = {
        "M": "NM",
        "NM": "NM",
        "SP": "SP",
        "MP": "MP",
        "HP": "HP",
        "D": "DMG",
    }

    FOIL_EXTRA_IDS = {2, 31}

    def parse_offers_page(self, html: str) -> list[RawOffer]:
        stock = self._extract_js_json(html, "cards_stock")
        if stock:
            js_offers = self._parse_js_offers(html)
            if js_offers:
                return js_offers

        soup = BeautifulSoup(html, "lxml")
        offers: list[RawOffer] = []

        rows = soup.select(sel.OFFER_ROW)
        if not rows:
            rows = self._fallback_find_rows(soup)

        for i, row in enumerate(rows):
            try:
                offer = self._parse_row(row, i)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Failed to parse offer row {i}: {e}")

        return offers

    def _parse_js_offers(self, html: str) -> list[RawOffer]:
        stock = self._extract_js_json(html, "cards_stock")
        stores = self._extract_js_json(html, "cards_stores") or {}
        if not stock:
            return []

        editions = self._extract_js_json(html, "cards_editions") or []
        quality_map = self._build_lookup(self._extract_js_json(html, "dataQuality"))
        language_map = self._build_lookup(self._extract_js_json(html, "dataLanguage"))
        edition_by_id = {str(ed.get("id")): ed.get("name") for ed in editions if ed.get("id")}

        soup = BeautifulSoup(html, "lxml")
        html_prices = self._extract_html_prices_by_item_id(soup)

        offers: list[RawOffer] = []
        for item in stock:
            try:
                offer = self._parse_js_stock_item(
                    item,
                    stores,
                    edition_by_id,
                    quality_map,
                    language_map,
                    html_prices,
                )
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Failed to parse JS stock item {item.get('id')}: {e}")

        return offers

    def _extract_js_json(self, html: str, var_name: str) -> Any:
        marker = f"var {var_name} = "
        start = html.find(marker)
        if start == -1:
            return None

        start += len(marker)
        if start >= len(html):
            return None

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
                        logger.warning(f"Failed to parse JS var {var_name}")
                        return None
        return None

    def _parse_js_price(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        if "," in text:
            return parse_price(text)
        try:
            return float(text)
        except ValueError:
            return parse_price(text)

    def _extract_html_prices_by_item_id(self, soup: BeautifulSoup) -> dict[str, float]:
        prices: dict[str, float] = {}
        for row in soup.select(sel.MARKETPLACE_STORE):
            row_id = row.get("id", "")
            if not row_id.startswith("mpline_1_"):
                continue
            item_id = row_id.removeprefix("mpline_1_")
            price_el = row.select_one(sel.MARKETPLACE_PRICE)
            if not price_el:
                continue
            price = parse_price(price_el.get_text(" ", strip=True))
            if price is not None and price > 0:
                prices[item_id] = price
        return prices

    def _build_lookup(self, items: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
        if not items:
            return {}
        return {str(item.get("id")): item for item in items if item.get("id") is not None}

    def _parse_js_stock_item(
        self,
        item: dict[str, Any],
        stores: dict[str, Any],
        edition_by_id: dict[str, str | None],
        quality_map: dict[str, dict[str, Any]],
        language_map: dict[str, dict[str, Any]],
        html_prices: dict[str, float],
    ) -> RawOffer | None:
        price_text = item.get("precoFinal") or item.get("preco")
        price = self._parse_js_price(price_text)
        if price is None or price <= 0:
            item_id = str(item.get("id", ""))
            price = html_prices.get(item_id)
        if price is None or price <= 0:
            return None

        store_id = str(item.get("lj_id", ""))
        store = stores.get(store_id) or {}
        store_name = (store.get("lj_name") or "").strip()
        if not store_name:
            store_name = f"Loja {store_id}"

        qualid = str(item.get("qualid", ""))
        quality = quality_map.get(qualid, {})
        condition = self.QUALITY_ACRON_MAP.get(quality.get("acron", ""), "NM")

        idioma = str(item.get("idioma", ""))
        language_entry = language_map.get(idioma, {})
        language = language_entry.get("acron", "PT")
        if language == "PTEN":
            language = "PT"

        edition_id = str(item.get("idEdicao", ""))
        edition = edition_by_id.get(edition_id)

        extras = item.get("extras", 0)
        try:
            extras_id = int(extras)
        except (TypeError, ValueError):
            extras_id = 0
        is_foil = extras_id in self.FOIL_EXTRA_IDS

        quant_filter = item.get("quantFilter")
        quantity = int(quant_filter) if quant_filter else 1

        rating_raw = store.get("lj_ref")
        rating = float(rating_raw) if rating_raw else None

        item_hash = hashlib.md5(json.dumps(item, sort_keys=True).encode()).hexdigest()

        return RawOffer(
            store_ligamagic_id=store_id,
            store_name=store_name,
            store_slug=slugify(store_name),
            price=price,
            quantity=quantity,
            condition=condition,
            language=language,
            edition=edition,
            is_foil=is_foil,
            raw_html_hash=item_hash,
            store_city=store.get("lj_cidade"),
            store_state=store.get("lj_uf") or item.get("lj_uf"),
            store_rating=rating,
        )

    def _fallback_find_rows(self, soup: BeautifulSoup) -> list[Tag]:
        store_rows = soup.select("#marketplace-stores .store, .stores.container-tab-1 .store")
        if store_rows:
            return store_rows
        table = soup.select_one(sel.OFFER_TABLE)
        if table:
            return table.find_all("tr")[1:]
        return []

    def _parse_row(self, row: Tag, index: int) -> RawOffer | None:
        html_hash = hashlib.md5(str(row).encode()).hexdigest()
        classes = " ".join(row.get("class", []))
        if "store" in classes:
            return self._parse_store_row(row, html_hash, index)

        store_el = row.select_one(sel.OFFER_STORE_NAME) or row.select_one("a")
        if not store_el:
            logger.trace(f"Row {index}: no store element found")
            return None

        store_name = store_el.get_text(strip=True)
        if not store_name:
            return None

        store_href = store_el.get("href", "")
        store_id = self._extract_store_id(store_href) or slugify(store_name)

        price_el = row.select_one(sel.OFFER_PRICE)
        price_text = price_el.get_text(strip=True) if price_el else ""
        if not price_text:
            tds = row.find_all("td")
            for td in tds:
                text = td.get_text(strip=True)
                if "R$" in text or re.match(r"[\d.,]+", text):
                    price_text = text
                    break

        price = parse_price(price_text)
        if price is None or price <= 0:
            logger.trace(f"Row {index}: invalid price '{price_text}'")
            return None

        condition = self._parse_condition(row)
        language = self._parse_language(row)
        edition = self._parse_edition(row)
        quantity = self._parse_quantity(row)
        is_foil = self._detect_foil(row)

        return RawOffer(
            store_ligamagic_id=store_id,
            store_name=store_name,
            store_slug=slugify(store_name),
            price=price,
            quantity=quantity,
            condition=condition,
            language=language,
            edition=edition,
            is_foil=is_foil,
            raw_html_hash=html_hash,
        )

    def _parse_store_row(self, row: Tag, html_hash: str, index: int) -> RawOffer | None:
        tooltip = row.select_one(".container-tooltip-store-information")
        store_name_el = (
            row.select_one(".container-tooltip-store-information .store-name")
            or row.select_one(".store-name")
        )
        store_name = store_name_el.get_text(strip=True) if store_name_el else ""
        if not store_name and tooltip:
            store_name = tooltip.get_text(strip=True).split("\n", 1)[0].strip()
        if not store_name:
            logger.trace(f"Store row {index}: no store name")
            return None

        link = row.select_one("a[href*='vendedor'], a.go-store, .link-store a")
        store_href = link.get("href", "") if link else ""
        store_id = self._extract_store_id(store_href) or slugify(store_name)

        price_el = row.select_one(".new-price, .quantity-and-price .price")
        price_text = price_el.get_text(" ", strip=True) if price_el else ""
        price = parse_price(price_text)
        if price is None or price <= 0:
            logger.trace(f"Store row {index}: invalid price '{price_text}'")
            return None

        condition = "NM"
        for el in row.select(".infos-store-and-item"):
            text = el.get_text(strip=True).upper()
            if text in self.QUALITY_ACRON_MAP:
                condition = self.QUALITY_ACRON_MAP[text]
                break

        edition_el = row.select_one(".infos-store")
        edition = edition_el.get_text(strip=True) if edition_el else None

        city_el = row.select_one(".store-address")
        city_text = city_el.get_text(strip=True) if city_el else ""
        city, state = None, None
        if " - " in city_text:
            city, state = [part.strip() for part in city_text.split(" - ", 1)]

        return RawOffer(
            store_ligamagic_id=store_id,
            store_name=store_name,
            store_slug=slugify(store_name),
            price=price,
            quantity=1,
            condition=condition,
            language="PT",
            edition=edition,
            is_foil=self._detect_foil(row),
            raw_html_hash=html_hash,
            store_city=city,
            store_state=state,
        )

    def _extract_store_id(self, href: str) -> str | None:
        match = re.search(r"vendedor[=/](\d+)", href, re.I)
        if match:
            return match.group(1)
        match = re.search(r"[?&]id=(\d+)", href)
        return match.group(1) if match else None

    def _parse_condition(self, row: Tag) -> str:
        el = row.select_one(sel.OFFER_CONDITION)
        if el:
            text = el.get_text(strip=True).lower()
            for key, val in self.CONDITION_MAP.items():
                if key in text:
                    return val
        return "NM"

    def _parse_language(self, row: Tag) -> str:
        el = row.select_one(sel.OFFER_LANGUAGE)
        if el:
            text = el.get_text(strip=True).lower()
            for key, val in self.LANGUAGE_MAP.items():
                if key in text:
                    return val
        return "PT"

    def _parse_edition(self, row: Tag) -> str | None:
        el = row.select_one(sel.OFFER_EDITION)
        if el:
            text = el.get_text(strip=True)
            return text if text else None
        return None

    def _parse_quantity(self, row: Tag) -> int:
        el = row.select_one(sel.OFFER_QUANTITY)
        if el:
            text = el.get_text(strip=True)
            match = re.search(r"\d+", text)
            if match:
                return int(match.group())
        return 1

    def _detect_foil(self, row: Tag) -> bool:
        text = row.get_text(strip=True).lower()
        return "foil" in text or "foil" in str(row.get("class", [])).lower()

    def get_page_card_names(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        names: list[str] = []
        for selector in (".item-name-en", ".item-name"):
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text and text not in names:
                    names.append(text)
        return names

    def page_matches_search(self, html: str, card_name: str) -> bool:
        if self._extract_js_json(html, "cards_stock") is None:
            return True
        names = self.get_page_card_names(html)
        if not names:
            return True
        return any(self.score_card_match(card_name, name) >= 95 for name in names)

    def score_card_match(self, card_name: str, candidate: str, href: str = "") -> int:
        from rapidfuzz import fuzz
        from urllib.parse import parse_qs, unquote_plus, urlparse

        target = normalize_text(card_name).lower()
        text = normalize_text(candidate).lower()
        if text == target:
            return 100

        if href:
            card_param = parse_qs(urlparse(href).query).get("card", [""])[0]
            if normalize_text(unquote_plus(card_param)).lower() == target:
                return 1000

        if "//" in text and "//" not in card_name:
            return 80
        if "(" in text and "(" not in card_name:
            return 80

        ratio = int(fuzz.ratio(target, text))
        if len(text) > len(target) + 10:
            ratio = max(0, ratio - 15)
        return ratio

    def is_captcha(self, html: str) -> bool:
        soup = BeautifulSoup(html, "lxml")
        return bool(soup.select_one(sel.CAPTCHA_CONTAINER))

    def is_not_found(self, html: str) -> bool:
        if self._extract_js_json(html, "cards_stock") is not None:
            return False

        soup = BeautifulSoup(html, "lxml")
        if soup.select_one(sel.CARD_NOT_FOUND):
            return True
        text = soup.get_text().lower()
        return "nenhum resultado" in text or "carta não encontrada" in text

    def extract_card_url_from_search(self, html: str, card_name: str) -> str | None:
        from rapidfuzz import fuzz
        from urllib.parse import parse_qs, unquote_plus, urlparse

        soup = BeautifulSoup(html, "lxml")
        normalized_target = normalize_text(card_name).lower()

        for link in soup.select("div.mtg-name-aux a[href*='view=cards/card']"):
            href = link.get("href")
            text = normalize_text(link.get_text(strip=True)).lower()
            if href and text == normalized_target:
                return href

        for link in soup.select("a[href*='view=cards/card']"):
            href = link.get("href")
            if not href:
                continue
            card_param = parse_qs(urlparse(href).query).get("card", [""])[0]
            if normalize_text(unquote_plus(card_param)).lower() == normalized_target:
                return href

        best_ratio = 0
        best_url = None
        for link in soup.select("a[href*='view=cards/card']"):
            text = normalize_text(link.get_text(strip=True)).lower()
            if not text:
                continue
            if text == normalized_target:
                return link.get("href")
            if "//" in text and "//" not in card_name:
                continue
            if "(" in text and "(" not in card_name:
                continue

            ratio = fuzz.ratio(normalized_target, text)
            if len(text) > len(normalized_target) + 10:
                ratio = max(0, ratio - 15)
            if ratio > best_ratio:
                best_ratio = ratio
                best_url = link.get("href")

        return best_url if best_ratio >= 85 else None
