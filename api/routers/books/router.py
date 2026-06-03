import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from psycopg_pool import AsyncConnectionPool
import psycopg
from pgvector.psycopg import register_vector_async

from db import get_pool
from shared.embeddings import embed
from .models import IngestResponse, BookSummary, SearchResult, SearchResponse
from .pipeline import ingest_epub, embed_book_chunks

router = APIRouter(prefix="/books", tags=["books"])


async def get_conn(pool: AsyncConnectionPool = Depends(get_pool)):
    async with pool.connection() as conn:
        yield conn


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(..., description="EPUB file to ingest"),
    max_tokens: int = Query(450, description="Approx words per chunk"),
    overlap_tokens: int = Query(80, description="Approx word overlap between chunks"),
    embed: bool = Query(True, description="Generate embeddings immediately"),
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """
    Upload an EPUB and ingest it into the knowledge base.
    Extracts chapters, chunks text, stores in Postgres, and embeds via OpenAI.
    """
    if not file.filename or not file.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=400, detail="File must be an .epub")

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = await ingest_epub(
            epub_path=tmp_path,
            conn=conn,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            do_embed=embed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return IngestResponse(
        **result,
        message="Ingestion complete" if embed else "Text ingested — run embed to generate vectors",
    )


@router.post("/{book_slug}/embed", response_model=dict)
async def embed_book(book_slug: str, conn: psycopg.AsyncConnection = Depends(get_conn)):
    """Generate (or re-generate) embeddings for all unembedded chunks of a book."""
    count = await embed_book_chunks(book_slug, conn)
    await conn.commit()
    return {"book_slug": book_slug, "chunks_embedded": count}


@router.get("/list", response_model=list[BookSummary])
async def list_books(conn: psycopg.AsyncConnection = Depends(get_conn)):
    """List all books with chunk and embedding counts."""
    rows = await conn.execute("""
        SELECT
            b.book_slug, b.title, b.author, b.extracted_at,
            COUNT(c.chunk_id)::int AS total_chunks,
            COUNT(c.embedding)::int AS embedded_chunks
        FROM books.books b
        LEFT JOIN books.chunks c ON b.book_slug = c.book_slug
        GROUP BY b.book_slug, b.title, b.author, b.extracted_at
        ORDER BY b.title
    """)
    return [
        BookSummary(
            book_slug=r[0], title=r[1], author=r[2], extracted_at=r[3],
            total_chunks=r[4], embedded_chunks=r[5],
        )
        for r in await rows.fetchall()
    ]


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str,
    limit: int = 5,
    threshold: float = 0.3,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """Semantic search across all ingested books."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    await register_vector_async(conn)
    query_embedding = await embed(q)

    rows = await conn.execute("""
        SELECT
            mc.chunk_id, mc.book_slug, b.title,
            mc.chapter_title, mc.text, mc.similarity
        FROM books.match_chunks(%s::vector, %s, %s) mc
        JOIN books.books b ON b.book_slug = mc.book_slug
    """, (query_embedding, threshold, limit))

    results = [
        SearchResult(
            chunk_id=r[0], book_slug=r[1], title=r[2],
            chapter_title=r[3], text=r[4], similarity=r[5],
        )
        for r in await rows.fetchall()
    ]
    return SearchResponse(query=q, results=results)
