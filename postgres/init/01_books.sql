-- ─────────────────────────────────────────────────────────────────────────────
-- Books schema
-- Stores ingested EPUB content as overlapping text chunks with embeddings.
-- Embedding model: text-embedding-3-large (3072 dimensions)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS books;

-- Book metadata (one row per EPUB)
CREATE TABLE IF NOT EXISTS books.books (
    book_slug        text        PRIMARY KEY,
    title            text,
    author           text,
    language         text,
    publisher        text,
    isbn             text,
    source_epub_path text,
    extracted_at     timestamptz
);

-- Text chunks with embeddings (many rows per book)
CREATE TABLE IF NOT EXISTS books.chunks (
    chunk_id                text    PRIMARY KEY,
    book_slug               text    REFERENCES books.books(book_slug) ON DELETE CASCADE,

    -- Chapter context
    chapter_order           int,
    chapter_id              text,
    chapter_title           text,
    chapter_file            text,
    chapter_href            text,

    -- Chunking metadata
    chunk_index             int,
    chunk_strategy          text,
    approx_tokens           int,
    max_tokens              int,
    overlap_tokens          int,
    start_paragraph         int,
    end_paragraph_exclusive int,

    -- Content
    text_sha256             text,
    text                    text,

    -- Embeddings
    embedding               vector(3072),
    embedding_model         text
);

-- Semantic search function
CREATE OR REPLACE FUNCTION books.match_chunks(
    query_embedding vector(3072),
    match_threshold float,
    match_count     int
)
RETURNS TABLE (
    chunk_id      text,
    book_slug     text,
    chapter_title text,
    text          text,
    similarity    float
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.chunk_id,
        c.book_slug,
        c.chapter_title,
        c.text,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM books.chunks c
    WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
