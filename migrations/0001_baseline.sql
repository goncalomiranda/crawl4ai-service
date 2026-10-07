-- depends:
-- Baseline of the schema the application already uses. Idempotent so it is a
-- no-op on production and builds a fresh test database. Column types for
-- crawled_content are inferred from application SQL; verify against production.
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS crawled_content (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
