-- Cube Budget Optimizer - Database Schema
-- Version: 1

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name        TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    ligamagic_id    TEXT,
    ligamagic_url   TEXT,
    color           TEXT,
    card_type       TEXT,
    mana_cost       TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(normalized_name)
);

CREATE TABLE IF NOT EXISTS stores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ligamagic_id TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    slug         TEXT NOT NULL UNIQUE,
    rating       REAL,
    city         TEXT,
    state        TEXT,
    is_active    INTEGER DEFAULT 1,
    first_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS offers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id         INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    store_id        INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    price           REAL NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 0,
    condition       TEXT NOT NULL DEFAULT 'NM',
    language        TEXT NOT NULL DEFAULT 'EN',
    edition         TEXT,
    is_foil         INTEGER DEFAULT 0,
    scraped_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_html_hash   TEXT,
    UNIQUE(card_id, store_id, condition, language, edition, is_foil)
);

CREATE TABLE IF NOT EXISTS cache_entries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id            INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE UNIQUE,
    last_scraped_at    DATETIME NOT NULL,
    scrape_duration_ms INTEGER,
    offers_found       INTEGER DEFAULT 0,
    status             TEXT DEFAULT 'ok',
    error_message      TEXT,
    ttl_hours          INTEGER DEFAULT 24
);

CREATE TABLE IF NOT EXISTS optimization_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_uuid        TEXT NOT NULL UNIQUE,
    input_file      TEXT,
    total_cards     INTEGER,
    found_cards     INTEGER,
    missing_cards   INTEGER,
    solver_used     TEXT,
    stores_count    INTEGER,
    total_price     REAL,
    greedy_stores   INTEGER,
    greedy_price    REAL,
    duration_ms     INTEGER,
    status          TEXT DEFAULT 'pending',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);

CREATE TABLE IF NOT EXISTS optimization_assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    card_id     INTEGER NOT NULL REFERENCES cards(id),
    store_id    INTEGER NOT NULL REFERENCES stores(id),
    offer_id    INTEGER NOT NULL REFERENCES offers(id),
    price       REAL NOT NULL,
    UNIQUE(run_id, card_id)
);

CREATE TABLE IF NOT EXISTS missing_cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    raw_name    TEXT NOT NULL,
    reason      TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_offers_card_id        ON offers(card_id);
CREATE INDEX IF NOT EXISTS idx_offers_store_id       ON offers(store_id);
CREATE INDEX IF NOT EXISTS idx_offers_price          ON offers(price);
CREATE INDEX IF NOT EXISTS idx_offers_scraped_at      ON offers(scraped_at);
CREATE INDEX IF NOT EXISTS idx_cache_last_scraped    ON cache_entries(last_scraped_at);
CREATE INDEX IF NOT EXISTS idx_cards_normalized      ON cards(normalized_name);
CREATE INDEX IF NOT EXISTS idx_assignments_run_id    ON optimization_assignments(run_id);
CREATE INDEX IF NOT EXISTS idx_assignments_store_id  ON optimization_assignments(store_id);
