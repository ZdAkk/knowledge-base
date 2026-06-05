import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from psycopg_pool import AsyncConnectionPool
import psycopg
from pgvector.psycopg import register_vector_async

from db import get_pool
from shared.embeddings import embed
from .models import IngestResponse, BookSummary, BookDetail, BookChapter, BookChunkItem, BookChunkDetail, SearchResult, SearchResponse
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


@router.get("/{book_slug}", response_model=BookDetail)
async def get_book(book_slug: str, conn: psycopg.AsyncConnection = Depends(get_conn)):
    """Full book record with metadata and chapter list."""
    row = await conn.execute("""
        SELECT b.book_slug, b.title, b.author, b.language, b.publisher, b.isbn, b.extracted_at,
               COUNT(c.chunk_id)::int AS total_chunks,
               COUNT(c.embedding)::int AS embedded_chunks
        FROM books.books b
        LEFT JOIN books.chunks c ON b.book_slug = c.book_slug
        WHERE b.book_slug = %s
        GROUP BY b.book_slug, b.title, b.author, b.language, b.publisher, b.isbn, b.extracted_at
    """, (book_slug,))
    book = await row.fetchone()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book '{book_slug}' not found")

    chapters_rows = await conn.execute("""
        SELECT chapter_title, chapter_order, COUNT(*)::int AS chunk_count
        FROM books.chunks
        WHERE book_slug = %s
        GROUP BY chapter_title, chapter_order
        ORDER BY chapter_order
    """, (book_slug,))
    chapters = [
        BookChapter(chapter_title=r[0], chapter_order=r[1], chunk_count=r[2])
        for r in await chapters_rows.fetchall()
    ]

    return BookDetail(
        book_slug=book[0], title=book[1], author=book[2],
        language=book[3], publisher=book[4], isbn=book[5],
        extracted_at=book[6], total_chunks=book[7], embedded_chunks=book[8],
        chapters=chapters,
    )


@router.get("/{book_slug}/chunks", response_model=list[BookChunkItem])
async def list_book_chunks(
    book_slug: str,
    chapter_order: int | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """List chunks for a book, optionally filtered by chapter_order."""
    filters = ["book_slug = %s"]
    params: list = [book_slug]
    if chapter_order is not None:
        filters.append("chapter_order = %s")
        params.append(chapter_order)
    params += [limit, offset]

    rows = await conn.execute(f"""
        SELECT chunk_id, chunk_index, chapter_title, chapter_order, approx_tokens, text
        FROM books.chunks
        WHERE {" AND ".join(filters)}
        ORDER BY chunk_index
        LIMIT %s OFFSET %s
    """, params)

    return [
        BookChunkItem(
            chunk_id=r[0], chunk_index=r[1], chapter_title=r[2],
            chapter_order=r[3], approx_tokens=r[4], text=r[5],
        )
        for r in await rows.fetchall()
    ]


@router.get("/{book_slug}/chunks/{chunk_id}", response_model=BookChunkDetail)
async def get_book_chunk(
    book_slug: str,
    chunk_id: str,
    conn: psycopg.AsyncConnection = Depends(get_conn),
):
    """Single chunk with prev/next navigation."""
    row = await conn.execute("""
        SELECT c.chunk_id, c.chunk_index, c.book_slug, b.title, b.author,
               c.chapter_title, c.chapter_order, c.approx_tokens, c.text
        FROM books.chunks c
        JOIN books.books b ON b.book_slug = c.book_slug
        WHERE c.chunk_id = %s AND c.book_slug = %s
    """, (chunk_id, book_slug))
    chunk = await row.fetchone()
    if not chunk:
        raise HTTPException(status_code=404, detail=f"Chunk '{chunk_id}' not found")

    # Prev / next within same chapter
    prev_row = await conn.execute("""
        SELECT chunk_id FROM books.chunks
        WHERE book_slug = %s AND chapter_order = %s AND chunk_index = %s
    """, (book_slug, chunk[6], chunk[1] - 1))
    prev_chunk = await prev_row.fetchone()

    next_row = await conn.execute("""
        SELECT chunk_id FROM books.chunks
        WHERE book_slug = %s AND chapter_order = %s AND chunk_index = %s
    """, (book_slug, chunk[6], chunk[1] + 1))
    next_chunk = await next_row.fetchone()

    return BookChunkDetail(
        chunk_id=chunk[0], chunk_index=chunk[1], book_slug=chunk[2],
        book_title=chunk[3], book_author=chunk[4], chapter_title=chunk[5],
        chapter_order=chunk[6], approx_tokens=chunk[7], text=chunk[8],
        prev_chunk_id=prev_chunk[0] if prev_chunk else None,
        next_chunk_id=next_chunk[0] if next_chunk else None,
    )
