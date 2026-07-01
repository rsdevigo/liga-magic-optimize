"""Text normalization utilities."""

from __future__ import annotations

import re

from unidecode import unidecode


def normalize_text(text: str) -> str:
    """Normalize card name for matching and storage."""
    text = unidecode(text.strip())
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-'/]", "", text)
    return text.strip()


def slugify(text: str) -> str:
    """Create URL-safe slug from text."""
    text = normalize_text(text)
    text = re.sub(r"[\s'/]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def parse_price(text: str) -> float | None:
    """Parse Brazilian price string to float."""
    if not text:
        return None
    cleaned = text.replace("R$", "").strip()
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None
