"""Integration tests for database repositories."""

from cube_budget.core.models import (
    AssignedCard,
    Card,
    MissingCardRecord,
    Offer,
    OptimizationResult,
    Store,
)


class TestDatabase:
    def test_card_upsert(self, card_repo):
        card = Card(raw_name="Lightning Bolt", normalized_name="lightning bolt")
        saved = card_repo.upsert(card)
        assert saved.id is not None
        assert saved.raw_name == "Lightning Bolt"

        updated = card_repo.upsert(
            Card(raw_name="Lightning Bolt (M11)", normalized_name="lightning bolt")
        )
        assert updated.id == saved.id

    def test_store_upsert(self, store_repo):
        store = Store(ligamagic_id="101", name="CardShop", slug="cardshop")
        saved = store_repo.upsert(store)
        assert saved.id is not None

    def test_offer_upsert(self, card_repo, store_repo, offer_repo):
        card = card_repo.upsert(Card(raw_name="A", normalized_name="a"))
        store = store_repo.upsert(Store(ligamagic_id="1", name="S", slug="s"))
        offer = offer_repo.upsert(
            Offer(card_id=card.id, store_id=store.id, price=10.0, quantity=1)  # type: ignore
        )
        assert offer.id is not None

    def test_run_lifecycle(self, card_repo, store_repo, offer_repo, run_repo):
        card = card_repo.upsert(Card(raw_name="A", normalized_name="a"))
        store = store_repo.upsert(Store(ligamagic_id="1", name="S", slug="s"))
        offer = offer_repo.upsert(
            Offer(card_id=card.id, store_id=store.id, price=5.0, quantity=1)  # type: ignore
        )

        run = run_repo.create_run("test-uuid-123", "cube.txt")
        assert run.status == "running"

        result = OptimizationResult(
            run_uuid="test-uuid-123",
            assignments=[
                AssignedCard(
                    card=card,
                    store=store,
                    offer=offer,
                    price=5.0,
                )
            ],
            missing=[MissingCardRecord(raw_name="Missing", reason="not_found")],
            stores_used=1,
            total_price=5.0,
            solver="greedy",
            duration_ms=100,
            total_cards=2,
            found_cards=1,
        )

        run_repo.complete_run(run.id, result)  # type: ignore
        run_repo.save_assignments(run.id, result.assignments)  # type: ignore
        run_repo.save_missing(run.id, result.missing)  # type: ignore

        loaded = run_repo.load_result("test-uuid-123")
        assert loaded is not None
        assert loaded.found_cards == 1
        assert len(loaded.missing) == 1

    def test_cache_repo(self, cache_repo, card_repo):
        from datetime import datetime

        from cube_budget.core.models import CacheEntry

        card = card_repo.upsert(Card(raw_name="A", normalized_name="a"))
        entry = CacheEntry(
            card_id=card.id,  # type: ignore
            last_scraped_at=datetime.now(),
            offers_found=3,
        )
        cache_repo.upsert(entry)
        assert cache_repo.is_valid(card.id)  # type: ignore
