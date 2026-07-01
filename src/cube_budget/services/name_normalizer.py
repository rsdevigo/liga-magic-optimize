"""Card name normalization service."""

from __future__ import annotations

from cube_budget.core.models import Card
from cube_budget.utils.text import normalize_text


class NameNormalizer:
    """Normalizes Magic card names for consistent matching."""

    def normalize(self, raw_name: str) -> str:
        return normalize_text(raw_name)

    def to_card(self, raw_name: str) -> Card:
        normalized = self.normalize(raw_name)
        return Card(raw_name=raw_name.strip(), normalized_name=normalized)

    def normalize_batch(self, raw_names: list[str]) -> list[Card]:
        seen: set[str] = set()
        cards: list[Card] = []
        for name in raw_names:
            normalized = self.normalize(name)
            if normalized not in seen:
                seen.add(normalized)
                cards.append(Card(raw_name=name.strip(), normalized_name=normalized))
        return cards
