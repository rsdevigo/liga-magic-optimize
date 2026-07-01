"""Build Carta x Loja matrix from optimization input."""

from __future__ import annotations

import math

from cube_budget.core.constants import CONDITION_RANK
from cube_budget.core.models import OptimizationInput
from cube_budget.optimizer.result import SolverInput


class MatrixBuilder:
    """Builds solver input matrix from offers data."""

    def build(self, opt_input: OptimizationInput) -> SolverInput:
        cards = opt_input.cards
        card_ids = [c.id for c in cards if c.id is not None]
        card_names = [c.raw_name for c in cards if c.id is not None]
        card_id_to_idx = {cid: i for i, cid in enumerate(card_ids)}

        # Collect unique stores from offers
        store_id_set: set[int] = set()
        for offer in opt_input.offers:
            if offer.store_id not in store_id_set:
                store_id_set.add(offer.store_id)

        store_ids = sorted(store_id_set)
        store_id_to_idx = {sid: j for j, sid in enumerate(store_ids)}

        store_names = []
        store_map = {s.id: s.name for s in opt_input.stores if s.id}
        for sid in store_ids:
            store_names.append(store_map.get(sid, f"Store_{sid}"))

        n_cards = len(card_ids)
        n_stores = len(store_ids)

        availability = [[0] * n_stores for _ in range(n_cards)]
        prices = [[math.inf] * n_stores for _ in range(n_cards)]

        min_rank = CONDITION_RANK.get(opt_input.min_condition, 0)

        for offer in opt_input.offers:
            if offer.card_id not in card_id_to_idx:
                continue
            if offer.store_id not in store_id_to_idx:
                continue

            if opt_input.ignore_foil and offer.is_foil:
                continue

            if offer.quantity < opt_input.min_stock:
                continue

            offer_rank = CONDITION_RANK.get(offer.condition, 99)
            if offer_rank > min_rank:
                continue

            if opt_input.preferred_language != "any":
                if offer.language != opt_input.preferred_language:
                    continue

            i = card_id_to_idx[offer.card_id]
            j = store_id_to_idx[offer.store_id]

            availability[i][j] = 1
            if offer.price < prices[i][j]:
                prices[i][j] = offer.price

        return SolverInput(
            card_ids=card_ids,
            card_names=card_names,
            store_ids=store_ids,
            store_names=store_names,
            availability=availability,
            prices=prices,
            max_stores=opt_input.max_stores,
        )

    def get_uncovered_cards(self, data: SolverInput) -> list[str]:
        """Return card names with no available offers."""
        uncovered = []
        for i, name in enumerate(data.card_names):
            if not any(data.availability[i]):
                uncovered.append(name)
        return uncovered
