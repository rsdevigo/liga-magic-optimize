"""Card repository."""

from __future__ import annotations

from datetime import datetime

from cube_budget.core.models import Card
from cube_budget.database.connection import DatabaseConnection


class CardRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def _row_to_card(self, row) -> Card:
        return Card(
            id=row["id"],
            raw_name=row["raw_name"],
            normalized_name=row["normalized_name"],
            ligamagic_id=row["ligamagic_id"],
            ligamagic_url=row["ligamagic_url"],
            color=row["color"],
            card_type=row["card_type"],
            mana_cost=row["mana_cost"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def upsert(self, card: Card) -> Card:
        conn = self._db.connect()
        existing = conn.execute(
            "SELECT * FROM cards WHERE normalized_name = ?",
            (card.normalized_name,),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE cards SET raw_name=?, ligamagic_id=?, ligamagic_url=?,
                   color=?, card_type=?, mana_cost=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (
                    card.raw_name,
                    card.ligamagic_id,
                    card.ligamagic_url,
                    card.color,
                    card.card_type,
                    card.mana_cost,
                    existing["id"],
                ),
            )
            conn.commit()
            return self.get_by_id(existing["id"])  # type: ignore

        cursor = conn.execute(
            """INSERT INTO cards (raw_name, normalized_name, ligamagic_id, ligamagic_url,
               color, card_type, mana_cost) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                card.raw_name,
                card.normalized_name,
                card.ligamagic_id,
                card.ligamagic_url,
                card.color,
                card.card_type,
                card.mana_cost,
            ),
        )
        conn.commit()
        return self.get_by_id(cursor.lastrowid)  # type: ignore

    def get_by_id(self, card_id: int) -> Card | None:
        row = self._db.connect().execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        return self._row_to_card(row) if row else None

    def get_by_normalized_name(self, name: str) -> Card | None:
        row = self._db.connect().execute(
            "SELECT * FROM cards WHERE normalized_name = ?", (name,)
        ).fetchone()
        return self._row_to_card(row) if row else None

    def get_by_ids(self, card_ids: list[int]) -> list[Card]:
        if not card_ids:
            return []
        placeholders = ",".join("?" * len(card_ids))
        rows = self._db.connect().execute(
            f"SELECT * FROM cards WHERE id IN ({placeholders})", card_ids
        ).fetchall()
        return [self._row_to_card(r) for r in rows]

    def count(self) -> int:
        row = self._db.connect().execute("SELECT COUNT(*) as c FROM cards").fetchone()
        return row["c"] if row else 0

    def get_all(self) -> list[Card]:
        rows = self._db.connect().execute("SELECT * FROM cards ORDER BY raw_name").fetchall()
        return [self._row_to_card(r) for r in rows]
