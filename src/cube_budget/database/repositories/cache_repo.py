"""Cache repository."""

from __future__ import annotations

from datetime import datetime, timedelta

from cube_budget.core.models import CacheEntry
from cube_budget.database.connection import DatabaseConnection


class CacheRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def _row_to_entry(self, row) -> CacheEntry:
        return CacheEntry(
            id=row["id"],
            card_id=row["card_id"],
            last_scraped_at=row["last_scraped_at"],
            scrape_duration_ms=row["scrape_duration_ms"],
            offers_found=row["offers_found"],
            status=row["status"],
            error_message=row["error_message"],
            ttl_hours=row["ttl_hours"],
        )

    def upsert(self, entry: CacheEntry) -> CacheEntry:
        conn = self._db.connect()
        conn.execute(
            """INSERT INTO cache_entries (card_id, last_scraped_at, scrape_duration_ms,
               offers_found, status, error_message, ttl_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(card_id) DO UPDATE SET
               last_scraped_at=excluded.last_scraped_at,
               scrape_duration_ms=excluded.scrape_duration_ms,
               offers_found=excluded.offers_found,
               status=excluded.status,
               error_message=excluded.error_message,
               ttl_hours=excluded.ttl_hours""",
            (
                entry.card_id,
                entry.last_scraped_at.isoformat(),
                entry.scrape_duration_ms,
                entry.offers_found,
                entry.status,
                entry.error_message,
                entry.ttl_hours,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM cache_entries WHERE card_id = ?", (entry.card_id,)
        ).fetchone()
        return self._row_to_entry(row)

    def get_by_card_id(self, card_id: int) -> CacheEntry | None:
        row = self._db.connect().execute(
            "SELECT * FROM cache_entries WHERE card_id = ?", (card_id,)
        ).fetchone()
        return self._row_to_entry(row) if row else None

    def is_valid(self, card_id: int) -> bool:
        entry = self.get_by_card_id(card_id)
        if not entry:
            return False
        if isinstance(entry.last_scraped_at, str):
            last = datetime.fromisoformat(entry.last_scraped_at)
        else:
            last = entry.last_scraped_at
        expiry = last + timedelta(hours=entry.ttl_hours)
        return datetime.now() < expiry

    def invalidate(self, card_id: int) -> None:
        self._db.connect().execute(
            "DELETE FROM cache_entries WHERE card_id = ?", (card_id,)
        )
        self._db.connect().commit()

    def invalidate_all(self) -> None:
        self._db.connect().execute("DELETE FROM cache_entries")
        self._db.connect().commit()

    def count(self) -> int:
        row = self._db.connect().execute("SELECT COUNT(*) as c FROM cache_entries").fetchone()
        return row["c"] if row else 0

    def count_valid(self) -> int:
        rows = self._db.connect().execute("SELECT card_id FROM cache_entries").fetchall()
        return sum(1 for r in rows if self.is_valid(r["card_id"]))
