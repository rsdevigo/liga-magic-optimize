"""Decode LigaMagic CSS sprite (imgnum) obfuscated prices."""

from __future__ import annotations

import itertools
import re

from bs4 import Tag

from cube_budget.utils.text import parse_price

CLASS_POS_RE = re.compile(
    r"\.([A-Za-z0-9_-]+)\{background-position:\s*(-?\d+)px\s+(-?\d+)px"
)
STYLE_BLOCK_RE = re.compile(r"<style>(.*?)</style>", re.DOTALL)


def build_class_to_pos(html: str) -> dict[str, tuple[int, int]]:
    css = "\n".join(STYLE_BLOCK_RE.findall(html))
    return {
        m.group(1): (int(m.group(2)), int(m.group(3)))
        for m in CLASS_POS_RE.finditer(css)
    }


def pos_key(x: int, y: int) -> str:
    return f"{x},{y}"


def resolve_pos(element: Tag, class_to_pos: dict[str, tuple[int, int]]) -> tuple[int, int] | None:
    for cls in element.get("class", []):
        if cls in class_to_pos:
            return class_to_pos[cls]
    style = element.get("style", "")
    match = re.search(r"background-position:\s*(-?\d+)px\s+(-?\d+)px", style)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def extract_price_tokens(price_el: Tag, class_to_pos: dict[str, tuple[int, int]]) -> list[str]:
    tokens: list[str] = []
    for child in price_el.find_all("div", recursive=False):
        classes = child.get("class", [])
        if "imgnum-monet" in classes:
            continue
        if "v2.png" in child.get("style", ""):
            tokens.append(",")
            continue
        pos = resolve_pos(child, class_to_pos)
        if pos:
            tokens.append(pos_key(*pos))
    return tokens


def _price_from_tokens(tokens: list[str], mapping: dict[str, str]) -> float | None:
    text = "".join("," if t == "," else mapping.get(t, "") for t in tokens)
    if "," not in text and len(text) >= 3:
        text = f"{text[:-2]},{text[-2:]}"
    return parse_price(f"R$ {text}")


def solve_digit_mapping(sequences: list[list[str]]) -> dict[str, str]:
    keys = sorted({k for seq in sequences for k in seq if k != ","})
    if not keys:
        return {}

    best_mapping: dict[str, str] = {}
    best_score = -1

    for perm in itertools.permutations("0123456789", len(keys)):
        mapping = dict(zip(keys, perm))
        score = 0
        for seq in sequences:
            price = _price_from_tokens(seq, mapping)
            if price is None or not 0.01 <= price <= 99_999.99:
                break
            score += 1
        else:
            if score > best_score:
                best_score = score
                best_mapping = mapping

    return best_mapping


def decode_image_price(
    price_el: Tag,
    class_to_pos: dict[str, tuple[int, int]],
    pos_to_digit: dict[str, str],
) -> str | None:
    tokens = extract_price_tokens(price_el, class_to_pos)
    if not tokens:
        return None
    text = "".join("," if t == "," else pos_to_digit.get(t, "") for t in tokens)
    if "," not in text and len(text) >= 3:
        text = f"{text[:-2]},{text[-2:]}"
    return text if parse_price(f"R$ {text}") is not None else None
