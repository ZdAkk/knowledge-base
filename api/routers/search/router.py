from fastapi import APIRouter, Depends, Query
import psycopg
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from db import get_pool
from shared.embeddings import embed
from .models import UnifiedSearchResult, UnifiedSearchResponse

router = APIRouter(prefix="/search", tags=["search"])


async def get_conn(pool: AsyncConnectionPool = Depends(get_pool)):
    async with pool.connection() as conn:
        yield conn


@router.get("", response_model=UnifiedSearchResponse)
async def unified_search(
    q: str,
    sources: str = Query("books,dreams", description="Comma-separated: books, dreams"),
    threshold: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(10, le=50),
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    Unified semantic search across all collections.
    sources: comma-separated list of collections to search (books, dreams).
    """
    await register_vector_async(conn)
    query_embedding = await embed(q)

    active_sources = {s.strip().lower() for s in sources.split(",")}

    parts = []
    params: list = []

    if "books" in active_sources:
        parts.append("""
            SELECT
                'book'::text AS source_type,
                c.chunk_id,
                c.book_slug AS source_id,
                b.title,
                c.chapter_title AS context,
                c.text,
                1 - (c.embedding <=> %s::vector) AS similarity
            FROM books.chunks c
            JOIN books.books b ON b.book_slug = c.book_slug
            WHERE 1 - (c.embedding <=> %s::vector) > %s
        """)
        params.extend([query_embedding, query_embedding, threshold])

    if "dreams" in active_sources:
        parts.append("""
            SELECT
                'dream'::text AS source_type,
                c.chunk_id,
                c.dream_id AS source_id,
                COALESCE(d.title, 'Dream — ' || d.dreamed_on::text) AS title,
                c.source_type AS context,
                c.text,
                1 - (c.embedding <=> %s::vector) AS similarity
            FROM dreams.chunks c
            JOIN dreams.dreams d ON d.dream_id = c.dream_id
            WHERE 1 - (c.embedding <=> %s::vector) > %s
        """)
        params.extend([query_embedding, query_embedding, threshold])

    if not parts:
        return UnifiedSearchResponse(query=q, results=[])

    sql = (
        " UNION ALL ".join(f"({p})" for p in parts)
        + " ORDER BY similarity DESC LIMIT %s"
    )
    params.append(limit)

    rows = await conn.execute(sql, params)
    results = [
        UnifiedSearchResult(
            source_type=r[0], chunk_id=r[1], source_id=r[2],
            title=r[3], context=r[4], text=r[5], similarity=r[6],
        )
        for r in await rows.fetchall()
    ]

    return UnifiedSearchResponse(query=q, results=results)
