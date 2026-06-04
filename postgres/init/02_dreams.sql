-- ─────────────────────────────────────────────────────────────────────────────
-- Dreams schema
-- Stores dream journal entries, Jungian interpretations, symbol analysis,
-- waking life connections, and semantic search chunks.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS dreams;

-- ── Core dream record ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dreams.dreams (
    dream_id        text        PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- When
    dreamed_on      date        NOT NULL,
    recorded_at     timestamptz DEFAULT now(),

    -- Content
    title           text,                       -- Auto-generated summary title
    raw_text        text        NOT NULL,        -- Exactly what you typed/said, unedited
    cleaned_text    text,                        -- Cleaned narrative after processing

    -- Metadata
    emotional_tone  text[],                     -- e.g. {fear, accomplishment, confusion}
    lucid           boolean     DEFAULT false,
    recurring       boolean     DEFAULT false,  -- Marked true if pattern seen before
    notes           text                        -- Any freeform notes you want to attach
);

-- ── Symbols and archetypes ────────────────────────────────────────────────────
-- One row per identified figure, object, or motif in a dream.

CREATE TABLE IF NOT EXISTS dreams.symbols (
    symbol_id       text        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    dream_id        text        NOT NULL REFERENCES dreams.dreams(dream_id) ON DELETE CASCADE,

    name            text        NOT NULL,   -- e.g. "The Heavyset Man", "The Slide"
    archetype       text,                   -- e.g. "The Shadow", "Wise Old Man", "Katabasis"
    description     text,                   -- What it was in the dream
    significance    text,                   -- What it means in the interpretation
    jungian_concept text                    -- Specific Jungian term if applicable
);

-- ── Interpretations ───────────────────────────────────────────────────────────
-- Full interpretation record. Multiple interpretations per dream are possible
-- (e.g. one from books, one updated after new context).

CREATE TABLE IF NOT EXISTS dreams.interpretations (
    interpretation_id   text        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    dream_id            text        NOT NULL REFERENCES dreams.dreams(dream_id) ON DELETE CASCADE,

    -- Core analysis
    central_theme       text,                   -- e.g. "The Ego Confronting the Shadow, Twice"
    jungian_analysis    text,                   -- Full Jungian interpretation text
    waking_life         text,                   -- Connection to current waking life
    message             text,                   -- The takeaway / psyche's message

    -- Sources used to generate this interpretation
    books_used          text[],                 -- book_slugs from books.books
    web_sources         text[],                 -- URLs used
    scholar_sources     text[],                 -- Academic references

    generated_at        timestamptz DEFAULT now(),
    model_used          text                    -- e.g. "claude-opus-4-5" if AI-generated
);

-- ── Chunks for semantic search ────────────────────────────────────────────────
-- Text chunks with embeddings, same pattern as books.chunks.
-- source_type distinguishes what part of the record the chunk came from.

CREATE TABLE IF NOT EXISTS dreams.chunks (
    chunk_id            text    PRIMARY KEY,
    dream_id            text    NOT NULL REFERENCES dreams.dreams(dream_id) ON DELETE CASCADE,

    -- What this chunk came from
    source_type         text    NOT NULL CHECK (source_type IN (
                                    'raw_dream',
                                    'cleaned_dream',
                                    'jungian_analysis',
                                    'waking_life',
                                    'symbol'
                                )),

    -- Chunking metadata
    chunk_index         int,
    chunk_strategy      text,
    approx_tokens       int,

    -- Content
    text_sha256         text,
    text                text,

    -- Embeddings
    embedding           vector(3072),
    embedding_model     text
);

-- ── Semantic search function ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION dreams.match_chunks(
    query_embedding vector(3072),
    match_threshold float,
    match_count     int,
    source_types    text[]  DEFAULT NULL   -- optional filter by source_type
)
RETURNS TABLE (
    chunk_id        text,
    dream_id        text,
    dreamed_on      date,
    title           text,
    source_type     text,
    text            text,
    similarity      float
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.chunk_id,
        c.dream_id,
        d.dreamed_on,
        d.title,
        c.source_type,
        c.text,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM dreams.chunks c
    JOIN dreams.dreams d ON d.dream_id = c.dream_id
    WHERE
        1 - (c.embedding <=> query_embedding) > match_threshold
        AND (source_types IS NULL OR c.source_type = ANY(source_types))
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
