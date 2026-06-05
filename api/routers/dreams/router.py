from datetime import date

import psycopg
from fastapi import APIRouter, HTTPException, Depends, Query
from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async

from db import get_pool
from shared.embeddings import embed

from .models import (
    DreamIngestRequest, DreamIngestResponse,
    InterpretationRequest, InterpretationResponse,
    DreamSummary, DreamDetail, SymbolOut, InterpretationOut,
    DreamSearchResponse, DreamSearchResult,
    ArchetypeSummary,
)
from .pipeline import ingest_dream, store_interpretation

router = APIRouter(prefix="/dreams", tags=["dreams"])


async def get_conn(pool: AsyncConnectionPool = Depends(get_pool)):
    async with pool.connection() as conn:
        yield conn


# ── Ingest ─────────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=DreamIngestResponse)
async def ingest(
    req: DreamIngestRequest,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    Store a dream entry. Accepts raw text immediately — cleaned text, title,
    and emotional tone are optional and can be provided by the automation
    pipeline after AI processing.
    """
    try:
        dream_id = await ingest_dream(req, conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return DreamIngestResponse(
        dream_id=dream_id,
        dreamed_on=req.dreamed_on,
        title=req.title,
        message="Dream stored successfully.",
    )


# ── Interpretation ─────────────────────────────────────────────────────────────

@router.post("/{dream_id}/interpretation", response_model=InterpretationResponse)
async def add_interpretation(
    dream_id: str,
    req: InterpretationRequest,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    Store the full interpretation for a dream (symbols, Jungian analysis,
    waking life connection). Chunks and embeds all text automatically.
    Called by the Trigger.dev automation after AI synthesis.
    """
    # Verify dream exists
    row = await conn.execute(
        "SELECT dream_id FROM dreams.dreams WHERE dream_id = %s", (dream_id,)
    )
    if not await row.fetchone():
        raise HTTPException(status_code=404, detail=f"Dream {dream_id} not found")

    try:
        interpretation_id, chunks_embedded = await store_interpretation(dream_id, req, conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return InterpretationResponse(
        interpretation_id=interpretation_id,
        dream_id=dream_id,
        chunks_embedded=chunks_embedded,
        message="Interpretation stored and embedded.",
    )


# ── List ───────────────────────────────────────────────────────────────────────

@router.get("/list", response_model=list[DreamSummary])
async def list_dreams(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """List all dreams, newest first. Optionally filter by date range."""
    filters = []
    params: list = []

    if from_date:
        filters.append(f"d.dreamed_on >= %s")
        params.append(from_date)
    if to_date:
        filters.append(f"d.dreamed_on <= %s")
        params.append(to_date)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    params += [limit, offset]

    rows = await conn.execute(f"""
        SELECT
            d.dream_id, d.dreamed_on, d.title, d.emotional_tone,
            d.lucid, d.recorded_at,
            COUNT(i.interpretation_id) > 0 AS has_interpretation
        FROM dreams.dreams d
        LEFT JOIN dreams.interpretations i ON i.dream_id = d.dream_id
        {where}
        GROUP BY d.dream_id, d.dreamed_on, d.title, d.emotional_tone, d.lucid, d.recorded_at
        ORDER BY d.dreamed_on DESC
        LIMIT %s OFFSET %s
    """, params)

    return [
        DreamSummary(
            dream_id=r[0], dreamed_on=r[1], title=r[2],
            emotional_tone=r[3], lucid=r[4], recorded_at=r[5],
            has_interpretation=r[6],
        )
        for r in await rows.fetchall()
    ]


# ── Detail ─────────────────────────────────────────────────────────────────────

@router.get("/{dream_id}", response_model=DreamDetail)
async def get_dream(
    dream_id: str,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """Full dream record including symbols and interpretation."""
    row = await conn.execute("""
        SELECT dream_id, dreamed_on, title, raw_text, cleaned_text,
               emotional_tone, lucid, recurring, notes, day_residue, recorded_at
        FROM dreams.dreams WHERE dream_id = %s
    """, (dream_id,))
    dream = await row.fetchone()
    if not dream:
        raise HTTPException(status_code=404, detail=f"Dream {dream_id} not found")

    # Symbols
    sym_rows = await conn.execute("""
        SELECT symbol_id, name, archetype, description, significance, jungian_concept
        FROM dreams.symbols WHERE dream_id = %s ORDER BY name
    """, (dream_id,))
    symbols = [
        SymbolOut(
            symbol_id=r[0], name=r[1], archetype=r[2],
            description=r[3], significance=r[4], jungian_concept=r[5],
        )
        for r in await sym_rows.fetchall()
    ]

    # Interpretation (most recent)
    int_row = await conn.execute("""
        SELECT interpretation_id, central_theme, jungian_analysis, waking_life,
               message, books_used, web_sources, scholar_sources, model_used, generated_at
        FROM dreams.interpretations
        WHERE dream_id = %s
        ORDER BY generated_at DESC LIMIT 1
    """, (dream_id,))
    interp_data = await int_row.fetchone()
    interpretation = InterpretationOut(
        interpretation_id=interp_data[0], central_theme=interp_data[1],
        jungian_analysis=interp_data[2], waking_life=interp_data[3],
        message=interp_data[4], books_used=interp_data[5],
        web_sources=interp_data[6], scholar_sources=interp_data[7],
        model_used=interp_data[8], generated_at=interp_data[9],
    ) if interp_data else None

    return DreamDetail(
        dream_id=dream[0], dreamed_on=dream[1], title=dream[2],
        raw_text=dream[3], cleaned_text=dream[4], emotional_tone=dream[5],
        lucid=dream[6], recurring=dream[7], notes=dream[8],
        day_residue=dream[9], recorded_at=dream[10],
        symbols=symbols, interpretation=interpretation,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────

@router.delete("/{dream_id}")
async def delete_dream(
    dream_id: str,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """Delete a dream and all associated symbols, interpretations, and chunks."""
    row = await conn.execute(
        "SELECT dream_id FROM dreams.dreams WHERE dream_id = %s", (dream_id,)
    )
    if not await row.fetchone():
        raise HTTPException(status_code=404, detail=f"Dream {dream_id} not found")

    await conn.execute("DELETE FROM dreams.dreams WHERE dream_id = %s", (dream_id,))
    await conn.commit()
    return {"dream_id": dream_id, "message": "Deleted."}


# ── Search ─────────────────────────────────────────────────────────────────────

@router.get("/search", response_model=DreamSearchResponse)
async def search_dreams(
    q: str,
    limit: int = Query(5, le=20),
    threshold: float = Query(0.3, ge=0.0, le=1.0),
    source_type: list[str] | None = Query(
        None,
        description="Filter by source: cleaned_dream, jungian_analysis, waking_life, symbol"
    ),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    Semantic search across dream chunks.
    Optionally filter by source_type (what part of the dream record to search)
    and/or date range.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    await register_vector_async(conn)
    query_embedding = await embed(q)

    # Build optional date filter
    date_filter = ""
    date_params: list = []
    if from_date:
        date_filter += " AND d.dreamed_on >= %s"
        date_params.append(from_date)
    if to_date:
        date_filter += " AND d.dreamed_on <= %s"
        date_params.append(to_date)

    rows = await conn.execute(f"""
        SELECT
            c.chunk_id, c.dream_id, d.dreamed_on, d.title,
            c.source_type, c.text,
            1 - (c.embedding <=> %s::vector) AS similarity
        FROM dreams.chunks c
        JOIN dreams.dreams d ON d.dream_id = c.dream_id
        WHERE
            1 - (c.embedding <=> %s::vector) > %s
            AND (%s::text[] IS NULL OR c.source_type = ANY(%s::text[]))
            {date_filter}
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    """, [
        query_embedding, query_embedding, threshold,
        source_type, source_type,
        *date_params,
        query_embedding, limit,
    ])

    results = [
        DreamSearchResult(
            chunk_id=r[0], dream_id=r[1], dreamed_on=r[2], title=r[3],
            source_type=r[4], text=r[5], similarity=r[6],
        )
        for r in await rows.fetchall()
    ]

    return DreamSearchResponse(query=q, results=results)


# ── Symbols / Archetypes ───────────────────────────────────────────────────────

@router.get("/symbols", response_model=list[ArchetypeSummary])
async def list_archetypes(
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    List all archetypes seen across all dreams, with how many times each
    appeared and which dreams contained them. Useful for spotting patterns.
    """
    rows = await conn.execute("""
        SELECT
            archetype,
            COUNT(*)::int AS count,
            array_agg(DISTINCT dream_id) AS dream_ids
        FROM dreams.symbols
        WHERE archetype IS NOT NULL
        GROUP BY archetype
        ORDER BY count DESC
    """)

    return [
        ArchetypeSummary(archetype=r[0], count=r[1], dream_ids=r[2])
        for r in await rows.fetchall()
    ]
