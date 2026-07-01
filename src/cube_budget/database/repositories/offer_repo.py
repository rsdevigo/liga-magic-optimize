"""Offer repository."""

from __future__ import annotations

from cube_budget.core.models import Offer
from cube_budget.database.connection import DatabaseConnection


class OfferRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def _row_to_offer(self, row) -> Offer:
        return Offer(
            id=row["id"],
            card_id=row["card_id"],
            store_id=row["store_id"],
            price=row["price"],
            quantity=row["quantity"],
            condition=row["condition"],
            language=row["language"],
            edition=row["edition"],
            is_foil=bool(row["is_foil"]),
            scraped_at=row["scraped_at"],
            raw_html_hash=row["raw_html_hash"],
            card_name=row["card_name"] if "card_name" in row.keys() else None,
            store_name=row["store_name"] if "store_name" in row.keys() else None,
        )

    def upsert(self, offer: Offer) -> Offer:
        conn = self._db.connect()
        conn.execute(
            """INSERT INTO offers (card_id, store_id, price, quantity, condition,
               language, edition, is_foil, raw_html_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(card_id, store_id, condition, language, edition, is_foil)
               DO UPDATE SET price=excluded.price, quantity=excluded.quantity,
               scraped_at=CURRENT_TIMESTAMP, raw_html_hash=excluded.raw_html_hash""",
            (
                offer.card_id,
                offer.store_id,
                offer.price,
                offer.quantity,
                offer.condition,
                offer.language,
                offer.edition,
                int(offer.is_foil),
                offer.raw_html_hash,
            ),
        )
        conn.commit()
        row = conn.execute(
            """SELECT * FROM offers WHERE card_id=? AND store_id=? AND condition=?
               AND language=? AND edition IS ? AND is_foil=?""",
            (
                offer.card_id,
                offer.store_id,
                offer.condition,
                offer.language,
                offer.edition,
                int(offer.is_foil),
            ),
        ).fetchone()
        return self._row_to_offer(row)

    def delete_for_card(self, card_id: int) -> None:
        conn = self._db.connect()
        conn.execute(
            """DELETE FROM optimization_assignments
               WHERE offer_id IN (SELECT id FROM offers WHERE card_id = ?)""",
            (card_id,),
        )
        conn.execute("DELETE FROM offers WHERE card_id = ?", (card_id,))
        conn.commit()

    def get_by_card_ids(self, card_ids: list[int]) -> list[Offer]:
        if not card_ids:
            return []
        placeholders = ",".join("?" * len(card_ids))
        rows = self._db.connect().execute(
            f"""SELECT o.*, c.raw_name as card_name, s.name as store_name
                FROM offers o
                JOIN cards c ON c.id = o.card_id
                JOIN stores s ON s.id = o.store_id
                WHERE o.card_id IN ({placeholders})""",
            card_ids,
        ).fetchall()
        return [self._row_to_offer(r) for r in rows]

    def count(self) -> int:
        row = self._db.connect().execute("SELECT COUNT(*) as c FROM offers").fetchone()
        return row["c"] if row else 0
