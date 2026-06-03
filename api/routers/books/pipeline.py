"""
EPUB ingestion pipeline.

Flow:
  EPUB file
    → extract chapters (ebooklib + markdownify)
    → chunk each chapter (paragraph sliding window)
    → upsert book + chunks into Postgres
    → embed chunks via OpenAI and write vectors back
"""

import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import markdownify

import psycopg
from pgvector.psycopg import register_vector_async

from shared.chunking import chunk_text
from shared.embeddings import embed_batch
from config import settings


# ─── Helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s or "book"


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style/nav
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()
    return markdownify.markdownify(str(soup), heading_style="ATX", strip=["a"])


def is_non_content(title: str, text: str, word_count: int) -> bool:
    """Skip obvious boilerplate chapters."""
    meta = title.lower()
    non_content_patterns = [
        "cover", "title page", "copyright", "table of contents",
        "contents", "also by", "about the author", "acknowledgment",
        "bibliography", "index", "imprint",
    ]
    if any(p in meta for p in non_content_patterns):
        return True
    if word_count < 100:
        return True
    return False


# ─── Core pipeline ────────────────────────────────────────────────────────────

async def ingest_epub(
    epub_path: str,
    conn: psycopg.AsyncConnection,
    max_tokens: int = 450,
    overlap_tokens: int = 80,
    do_embed: bool = True,
) -> dict:
    """
    Full pipeline for one EPUB file.
    Returns a summary dict with counts.
    """
    await register_vector_async(conn)
    path = Path(epub_path)
    if not path.exists():
        raise FileNotFoundError(f"EPUB not found: {epub_path}")

    book = epub.read_epub(str(path), options={"ignore_ncx": True})

    # ── Metadata
    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else path.stem
    author = book.get_metadata("DC", "creator")
    author = author[0][0] if author else None
    language = book.get_metadata("DC", "language")
    language = language[0][0] if language else None
    publisher = book.get_metadata("DC", "publisher")
    publisher = publisher[0][0] if publisher else None
    isbn_meta = book.get_metadata("DC", "identifier")
    isbn = None
    for val, attrs in (isbn_meta or []):
        if "isbn" in str(attrs).lower() or "isbn" in str(val).lower():
            isbn = val
            break

    book_slug = slugify(title)
    extracted_at = datetime.now(timezone.utc)

    # ── Upsert book row
    await conn.execute("""
        INSERT INTO books.books
            (book_slug, title, author, language, publisher, isbn, source_epub_path, extracted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (book_slug) DO UPDATE SET
            title = EXCLUDED.title,
            author = EXCLUDED.author,
            language = EXCLUDED.language,
            publisher = EXCLUDED.publisher,
            isbn = EXCLUDED.isbn,
            source_epub_path = EXCLUDED.source_epub_path,
            extracted_at = EXCLUDED.extracted_at
    """, (book_slug, title, author, language, publisher, isbn, str(path), extracted_at))

    # ── Extract chapters
    chapters = []
    for order, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
        try:
            html = item.get_content().decode("utf-8", errors="replace")
        except Exception:
            continue

        md = html_to_markdown(html)
        words = len(md.split())

        # Try to get title from first heading
        soup = BeautifulSoup(html, "html.parser")
        heading = soup.find(["h1", "h2", "h3"])
        chapter_title = heading.get_text(strip=True) if heading else f"Chapter {order + 1}"

        if is_non_content(chapter_title, md, words):
            continue

        chapters.append({
            "order": order,
            "id": item.get_id(),
            "title": chapter_title,
            "text": md,
        })

    # ── Chunk all chapters
    all_chunk_records = []
    for ch in chapters:
        chunks = chunk_text(ch["text"], max_tokens=max_tokens, overlap_tokens=overlap_tokens)
        for c in chunks:
            chunk_id = f"chunk_{book_slug}_{len(all_chunk_records):06d}"
            all_chunk_records.append({
                "chunk_id": chunk_id,
                "book_slug": book_slug,
                "chapter_order": ch["order"],
                "chapter_id": ch["id"],
                "chapter_title": ch["title"],
                "chunk_index": c.index,
                "chunk_strategy": "paragraph_window_v1",
                "approx_tokens": c.approx_tokens,
                "max_tokens": max_tokens,
                "overlap_tokens": overlap_tokens,
                "start_paragraph": c.start_paragraph,
                "end_paragraph_exclusive": c.end_paragraph_exclusive,
                "text_sha256": c.sha256,
                "text": c.text,
            })

    # ── Upsert chunks (text only, no embeddings yet)
    BATCH = 200
    async with conn.cursor() as cur:
        for i in range(0, len(all_chunk_records), BATCH):
            batch = all_chunk_records[i:i + BATCH]
            await cur.executemany("""
                INSERT INTO books.chunks (
                    chunk_id, book_slug,
                    chapter_order, chapter_id, chapter_title,
                    chunk_index, chunk_strategy,
                    approx_tokens, max_tokens, overlap_tokens,
                    start_paragraph, end_paragraph_exclusive,
                    text_sha256, text
                ) VALUES (
                    %(chunk_id)s, %(book_slug)s,
                    %(chapter_order)s, %(chapter_id)s, %(chapter_title)s,
                    %(chunk_index)s, %(chunk_strategy)s,
                    %(approx_tokens)s, %(max_tokens)s, %(overlap_tokens)s,
                    %(start_paragraph)s, %(end_paragraph_exclusive)s,
                    %(text_sha256)s, %(text)s
                )
                ON CONFLICT (chunk_id) DO UPDATE SET
                    text = EXCLUDED.text,
                    text_sha256 = EXCLUDED.text_sha256,
                    chapter_title = EXCLUDED.chapter_title
            """, batch)

    chunks_embedded = 0

    # ── Embed
    if do_embed:
        chunks_embedded = await embed_book_chunks(book_slug, conn)

    await conn.commit()

    return {
        "book_slug": book_slug,
        "title": title,
        "author": author,
        "chunks_ingested": len(all_chunk_records),
        "chunks_embedded": chunks_embedded,
    }


async def embed_book_chunks(
    book_slug: str,
    conn: psycopg.AsyncConnection,
    batch_size: int = 50,
) -> int:
    """Fetch unembedded chunks for a book, embed them, write vectors back."""
    await register_vector_async(conn)

    rows = await conn.execute("""
        SELECT chunk_id, text FROM books.chunks
        WHERE book_slug = %s AND embedding IS NULL
        ORDER BY chunk_index
    """, (book_slug,))
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
                UPDATE books.chunks
                SET embedding = %s, embedding_model = %s
                WHERE chunk_id = %s
            """, (vector, settings.embedding_model, chunk_id))
        total += len(batch)

    return total
