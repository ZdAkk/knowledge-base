"""
Dreams ingestion and interpretation pipeline.

Flow:
  POST /dreams/ingest
    → store dream record (raw + optional cleaned data)

  POST /dreams/{dream_id}/interpretation
    → store interpretation + symbols
    → chunk jungian_analysis, waking_life, cleaned_dream text
    → embed all chunks via OpenAI
"""

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import psycopg
from pgvector.psycopg import register_vector_async

from shared.chunking import chunk_text
from shared.embeddings import embed_batch
from config import settings

from .models import DreamIngestRequest, InterpretationRequest


# ── Ingest ─────────────────────────────────────────────────────────────────────

async def ingest_dream(
    req: DreamIngestRequest,
    conn: psycopg.AsyncConnection,
) -> str:
    """Store a dream record. Returns the generated dream_id."""
    dream_id = str(uuid4())
    recorded_at = datetime.now(timezone.utc)

    await conn.execute("""
        INSERT INTO dreams.dreams (
            dream_id, dreamed_on, recorded_at,
            title, raw_text, cleaned_text,
            emotional_tone, lucid, recurring, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        dream_id, req.dreamed_on, recorded_at,
        req.title, req.raw_text, req.cleaned_text,
        req.emotional_tone, req.lucid, req.recurring, req.notes,
    ))

    await conn.commit()
    return dream_id


# ── Interpretation ─────────────────────────────────────────────────────────────

async def store_interpretation(
    dream_id: str,
    req: InterpretationRequest,
    conn: psycopg.AsyncConnection,
) -> tuple[str, int]:
    """
    Store interpretation + symbols, then chunk and embed all text.
    Returns (interpretation_id, chunks_embedded).
    """
    await register_vector_async(conn)

    interpretation_id = str(uuid4())
    generated_at = datetime.now(timezone.utc)

    # ── Store interpretation
    await conn.execute("""
        INSERT INTO dreams.interpretations (
            interpretation_id, dream_id,
            central_theme, jungian_analysis, waking_life, message,
            books_used, web_sources, scholar_sources,
            model_used, generated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (interpretation_id) DO NOTHING
    """, (
        interpretation_id, dream_id,
        req.central_theme, req.jungian_analysis, req.waking_life, req.message,
        req.books_used, req.web_sources, req.scholar_sources,
        req.model_used, generated_at,
    ))

    # ── Store symbols
    if req.symbols:
        async with conn.cursor() as cur:
            await cur.executemany("""
                INSERT INTO dreams.symbols (
                    symbol_id, dream_id,
                    name, archetype, description, significance, jungian_concept
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol_id) DO NOTHING
            """, [
                (
                    str(uuid4()), dream_id,
                    s.name, s.archetype, s.description, s.significance, s.jungian_concept,
                )
                for s in req.symbols
            ])

    # ── Fetch dream text for chunking
    row = await conn.execute(
        "SELECT cleaned_text, raw_text FROM dreams.dreams WHERE dream_id = %s",
        (dream_id,)
    )
    dream_row = await row.fetchone()
    dream_text = dream_row[0] or dream_row[1]  # prefer cleaned, fall back to raw

    # ── Build chunks from all text sources
    chunk_records = []

    sources = [
        ("cleaned_dream", dream_text),
        ("jungian_analysis", req.jungian_analysis),
        ("waking_life", req.waking_life),
    ]

    for source_type, text in sources:
        if not text:
            continue
        chunks = chunk_text(text, max_tokens=400, overlap_tokens=60)
        for c in chunks:
            chunk_id = f"dream_{dream_id}_{source_type}_{c.index:04d}"
            chunk_records.append({
                "chunk_id": chunk_id,
                "dream_id": dream_id,
                "source_type": source_type,
                "chunk_index": c.index,
                "chunk_strategy": "paragraph_window_v1",
                "approx_tokens": c.approx_tokens,
                "text_sha256": c.sha256,
                "text": c.text,
            })

    # ── Upsert chunks (text only)
    if chunk_records:
        async with conn.cursor() as cur:
            await cur.executemany("""
                INSERT INTO dreams.chunks (
                    chunk_id, dream_id, source_type,
                    chunk_index, chunk_strategy, approx_tokens,
                    text_sha256, text
                ) VALUES (
                    %(chunk_id)s, %(dream_id)s, %(source_type)s,
                    %(chunk_index)s, %(chunk_strategy)s, %(approx_tokens)s,
                    %(text_sha256)s, %(text)s
                )
                ON CONFLICT (chunk_id) DO UPDATE SET
                    text = EXCLUDED.text,
                    text_sha256 = EXCLUDED.text_sha256
            """, chunk_records)

    # ── Embed all chunks
    chunks_embedded = await embed_dream_chunks(dream_id, conn)

    await conn.commit()
    return interpretation_id, chunks_embedded


async def embed_dream_chunks(
    dream_id: str,
    conn: psycopg.AsyncConnection,
    batch_size: int = 50,
) -> int:
    """Embed any unembedded chunks for a dream."""
    await register_vector_async(conn)

    rows = await conn.execute("""
        SELECT chunk_id, text FROM dreams.chunks
        WHERE dream_id = %s AND embedding IS NULL
        ORDER BY chunk_index
    """, (dream_id,))
    unembedded = await rows.fetchall()

    if not unembedded:
        return 0

    total = 0
    for i in range(0, len(unembedded), batch_size):
        batch = unembedded[i:i + batch_size]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]
        vectors = await embed_batch(texts)

        for chunk_id, vector in zip(ids, vectors):
            await conn.execute("""
                UPDATE dreams.chunks
                SET embedding = %s, embedding_model = %s
                WHERE chunk_id = %s
            """, (vector, settings.embedding_model, chunk_id))
        total += len(batch)

    return total
