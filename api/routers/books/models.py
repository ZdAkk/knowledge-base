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
