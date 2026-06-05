from typing import Literal
from pydantic import BaseModel


class UnifiedSearchResult(BaseModel):
    chunk_id: str
    source_type: Literal["book", "dream"]
    source_id: str          # book_slug or dream_id
    title: str | None       # book title or dream title
    context: str | None     # chapter_title for books, source_type for dreams
    text: str
    similarity: float


class UnifiedSearchResponse(BaseModel):
    query: str
    results: list[UnifiedSearchResult]
