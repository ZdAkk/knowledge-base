-- ─────────────────────────────────────────────────────────────────────────────
-- Extensions
-- Runs first (alphabetical order). Add any shared Postgres extensions here.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector: enables vector(n) column type and <=> operator

-- Migration tracking table — used by the migration runner to know what's been applied
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     text        PRIMARY KEY,
    applied_at  timestamptz DEFAULT now()
);
