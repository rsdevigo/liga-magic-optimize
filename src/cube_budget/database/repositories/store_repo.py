"""Store repository."""

from __future__ import annotations

import sqlite3

from cube_budget.core.models import Store
from cube_budget.database.connection import DatabaseConnection


class StoreRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def _row_to_store(self, row) -> Store:
        return Store(
            id=row["id"],
            ligamagic_id=row["ligamagic_id"],
            name=row["name"],
            slug=row["slug"],
            rating=row["rating"],
            city=row["city"],
            state=row["state"],
            is_active=bool(row["is_active"]),
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
        )

    def _resolve_slug(self, conn, store: Store, exclude_id: int | None = None) -> str:
        slug = store.slug
        query = "SELECT id, ligamagic_id FROM stores WHERE slug = ?"
        params: list[object] = [slug]
        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)

        existing = conn.execute(query, params).fetchone()
        if not existing or existing["ligamagic_id"] == store.ligamagic_id:
            return slug
        return f"{slug}-{store.ligamagic_id}"

    def upsert(self, store: Store) -> Store:
        conn = self._db.connect()
        existing = conn.execute(
            "SELECT id FROM stores WHERE ligamagic_id = ?", (store.ligamagic_id,)
        ).fetchone()

        slug = self._resolve_slug(
            conn, store, exclude_id=existing["id"] if existing else None
        )

        if existing:
            conn.execute(
                """UPDATE stores SET name=?, slug=?, rating=?, city=?, state=?,
                   is_active=?, last_seen=CURRENT_TIMESTAMP WHERE id=?""",
                (
                    store.name,
                    slug,
                    store.rating,
                    store.city,
                    store.state,
                    int(store.is_active),
                    existing["id"],
                ),
            )
            conn.commit()
            return self.get_by_id(existing["id"])  # type: ignore

        try:
            cursor = conn.execute(
                """INSERT INTO stores (ligamagic_id, name, slug, rating, city, state, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    store.ligamagic_id,
                    store.name,
                    slug,
                    store.rating,
                    store.city,
                    store.state,
                    int(store.is_active),
                ),
            )
            conn.commit()
            return self.get_by_id(cursor.lastrowid)  # type: ignore
        except sqlite3.IntegrityError:
            conn.rollback()
            slug = f"{slug}-{store.ligamagic_id}"
            cursor = conn.execute(
                """INSERT INTO stores (ligamagic_id, name, slug, rating, city, state, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    store.ligamagic_id,
                    store.name,
                    slug,
                    store.rating,
                    store.city,
                    store.state,
                    int(store.is_active),
                ),
            )
            conn.commit()
            return self.get_by_id(cursor.lastrowid)  # type: ignore

    def get_by_id(self, store_id: int) -> Store | None:
        row = self._db.connect().execute(
            "SELECT * FROM stores WHERE id = ?", (store_id,)
        ).fetchone()
        return self._row_to_store(row) if row else None

    def get_by_ids(self, store_ids: list[int]) -> list[Store]:
        if not store_ids:
            return []
        placeholders = ",".join("?" * len(store_ids))
        rows = self._db.connect().execute(
            f"SELECT * FROM stores WHERE id IN ({placeholders})", store_ids
        ).fetchall()
        return [self._row_to_store(r) for r in rows]

    def count(self) -> int:
        row = self._db.connect().execute("SELECT COUNT(*) as c FROM stores").fetchone()
        return row["c"] if row else 0

    def get_all(self) -> list[Store]:
        rows = self._db.connect().execute("SELECT * FROM stores ORDER BY name").fetchall()
        return [self._row_to_store(r) for r in rows]
