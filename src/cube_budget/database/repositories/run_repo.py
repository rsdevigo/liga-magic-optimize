"""Optimization run repository."""

from __future__ import annotations

from datetime import datetime

from cube_budget.core.models import (
    AssignedCard,
    Card,
    MissingCardRecord,
    Offer,
    OptimizationResult,
    OptimizationRunRecord,
    Store,
)
from cube_budget.database.connection import DatabaseConnection


class RunRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create_run(self, run_uuid: str, input_file: str | None = None) -> OptimizationRunRecord:
        conn = self._db.connect()
        cursor = conn.execute(
            """INSERT INTO optimization_runs (run_uuid, input_file, status)
               VALUES (?, ?, 'running')""",
            (run_uuid, input_file),
        )
        conn.commit()
        return self.get_by_id(cursor.lastrowid)  # type: ignore

    def update_run(self, run_id: int, **kwargs) -> None:
        if not kwargs:
            return
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [run_id]
        self._db.connect().execute(
            f"UPDATE optimization_runs SET {fields} WHERE id=?", values
        )
        self._db.connect().commit()

    def complete_run(
        self,
        run_id: int,
        result: OptimizationResult,
    ) -> None:
        self.update_run(
            run_id,
            total_cards=result.total_cards,
            found_cards=result.found_cards,
            missing_cards=len(result.missing),
            solver_used=result.solver,
            stores_count=result.stores_used,
            total_price=result.total_price,
            greedy_stores=result.greedy_stores,
            greedy_price=result.greedy_price,
            duration_ms=result.duration_ms,
            status="done",
            completed_at=datetime.now().isoformat(),
        )

    def save_assignments(self, run_id: int, assignments: list[AssignedCard]) -> None:
        conn = self._db.connect()
        for a in assignments:
            conn.execute(
                """INSERT OR REPLACE INTO optimization_assignments
                   (run_id, card_id, store_id, offer_id, price)
                   VALUES (?, ?, ?, ?, ?)""",
                (run_id, a.card.id, a.store.id, a.offer.id, a.price),
            )
        conn.commit()

    def save_missing(self, run_id: int, missing: list[MissingCardRecord]) -> None:
        conn = self._db.connect()
        for m in missing:
            conn.execute(
                "INSERT INTO missing_cards (run_id, raw_name, reason) VALUES (?, ?, ?)",
                (run_id, m.raw_name, m.reason),
            )
        conn.commit()

    def get_by_uuid(self, run_uuid: str) -> OptimizationRunRecord | None:
        row = self._db.connect().execute(
            "SELECT * FROM optimization_runs WHERE run_uuid = ?", (run_uuid,)
        ).fetchone()
        return self._row_to_run(row) if row else None

    def get_by_id(self, run_id: int) -> OptimizationRunRecord | None:
        row = self._db.connect().execute(
            "SELECT * FROM optimization_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return self._row_to_run(row) if row else None

    def get_latest(self) -> OptimizationRunRecord | None:
        row = self._db.connect().execute(
            "SELECT * FROM optimization_runs ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return self._row_to_run(row) if row else None

    def get_running(self) -> OptimizationRunRecord | None:
        row = self._db.connect().execute(
            "SELECT * FROM optimization_runs WHERE status = 'running' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return self._row_to_run(row) if row else None

    def get_recent(self, limit: int = 5) -> list[OptimizationRunRecord]:
        rows = self._db.connect().execute(
            "SELECT * FROM optimization_runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_run(r) for r in rows]

    def load_result(self, run_uuid: str) -> OptimizationResult | None:
        run = self.get_by_uuid(run_uuid)
        if not run or not run.id:
            return None

        conn = self._db.connect()
        assignment_rows = conn.execute(
            """SELECT oa.*, c.raw_name, c.normalized_name, c.ligamagic_url,
                      s.name as store_name, s.slug, s.ligamagic_id as store_lm_id,
                      o.condition, o.language, o.edition, o.is_foil, o.quantity
               FROM optimization_assignments oa
               JOIN cards c ON c.id = oa.card_id
               JOIN stores s ON s.id = oa.store_id
               JOIN offers o ON o.id = oa.offer_id
               WHERE oa.run_id = ?""",
            (run.id,),
        ).fetchall()

        missing_rows = conn.execute(
            "SELECT raw_name, reason FROM missing_cards WHERE run_id = ?", (run.id,)
        ).fetchall()

        assignments = []
        for row in assignment_rows:
            card = Card(
                id=row["card_id"],
                raw_name=row["raw_name"],
                normalized_name=row["normalized_name"],
                ligamagic_url=row["ligamagic_url"],
            )
            store = Store(
                id=row["store_id"],
                ligamagic_id=row["store_lm_id"],
                name=row["store_name"],
                slug=row["slug"],
            )
            offer = Offer(
                id=row["offer_id"],
                card_id=row["card_id"],
                store_id=row["store_id"],
                price=row["price"],
                quantity=row["quantity"],
                condition=row["condition"],
                language=row["language"],
                edition=row["edition"],
                is_foil=bool(row["is_foil"]),
            )
            assignments.append(
                AssignedCard(card=card, store=store, offer=offer, price=row["price"])
            )

        missing = [
            MissingCardRecord(raw_name=r["raw_name"], reason=r["reason"] or "not_found")
            for r in missing_rows
        ]

        return OptimizationResult(
            run_uuid=run.run_uuid,
            assignments=assignments,
            missing=missing,
            stores_used=run.stores_count or 0,
            total_price=run.total_price or 0.0,
            solver=run.solver_used or "unknown",
            duration_ms=run.duration_ms or 0,
            total_cards=run.total_cards or 0,
            found_cards=run.found_cards or 0,
            greedy_stores=run.greedy_stores,
            greedy_price=run.greedy_price,
            input_file=run.input_file,
            created_at=run.created_at,
        )

    def _row_to_run(self, row) -> OptimizationRunRecord:
        return OptimizationRunRecord(
            id=row["id"],
            run_uuid=row["run_uuid"],
            input_file=row["input_file"],
            total_cards=row["total_cards"],
            found_cards=row["found_cards"],
            missing_cards=row["missing_cards"],
            solver_used=row["solver_used"],
            stores_count=row["stores_count"],
            total_price=row["total_price"],
            greedy_stores=row["greedy_stores"],
            greedy_price=row["greedy_price"],
            duration_ms=row["duration_ms"],
            status=row["status"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )
