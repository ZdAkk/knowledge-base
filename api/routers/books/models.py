from pydantic import BaseModel
from datetime import datetime


class IngestResponse(BaseModel):
    book_slug: str
    title: str | None
    author: str | None
    chunks_ingested: int
    chunks_embedded: int
    message: str


class BookSummary(BaseModel):
    book_slug: str
    title: str | None
    author: str | None
    total_chunks: int
    embedded_chunks: int
    extracted_at: datetime | None


class BookChapter(BaseModel):
    chapter_title: str | None
    chapter_order: int
    chunk_count: int


class BookDetail(BaseModel):
    book_slug: str
    title: str | None
    author: str | None
    language: str | None
    publisher: str | None
    isbn: str | None
    extracted_at: datetime | None
    total_chunks: int
    embedded_chunks: int
    chapters: list[BookChapter]


class SearchResult(BaseModel):
    chunk_id: str
    book_slug: str
    title: str | None
    chapter_title: str | None
    text: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
