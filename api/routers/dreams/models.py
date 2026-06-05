from datetime import date, datetime
from pydantic import BaseModel


# ── Ingest ─────────────────────────────────────────────────────────────────────

class DreamIngestRequest(BaseModel):
    dreamed_on: date
    raw_text: str
    cleaned_text: str | None = None
    title: str | None = None
    emotional_tone: list[str] | None = None
    lucid: bool = False
    recurring: bool = False
    notes: str | None = None
    day_residue: str | None = None


class DreamIngestResponse(BaseModel):
    dream_id: str
    dreamed_on: date
    title: str | None
    message: str


# ── Interpretation ─────────────────────────────────────────────────────────────

class SymbolInput(BaseModel):
    name: str
    archetype: str | None = None
    description: str | None = None
    significance: str | None = None
    jungian_concept: str | None = None


class InterpretationRequest(BaseModel):
    central_theme: str
    jungian_analysis: str
    waking_life: str
    message: str
    symbols: list[SymbolInput] = []
    books_used: list[str] | None = None
    web_sources: list[str] | None = None
    scholar_sources: list[str] | None = None
    model_used: str | None = None


class InterpretationResponse(BaseModel):
    interpretation_id: str
    dream_id: str
    chunks_embedded: int
    message: str


# ── List & Detail ──────────────────────────────────────────────────────────────

class DreamSummary(BaseModel):
    dream_id: str
    dreamed_on: date
    title: str | None
    emotional_tone: list[str] | None
    lucid: bool
    has_interpretation: bool
    recorded_at: datetime


class SymbolOut(BaseModel):
    symbol_id: str
    name: str
    archetype: str | None
    description: str | None
    significance: str | None
    jungian_concept: str | None


class InterpretationOut(BaseModel):
    interpretation_id: str
    central_theme: str | None
    jungian_analysis: str | None
    waking_life: str | None
    message: str | None
    books_used: list[str] | None
    web_sources: list[str] | None
    scholar_sources: list[str] | None
    model_used: str | None
    generated_at: datetime


class DreamDetail(BaseModel):
    dream_id: str
    dreamed_on: date
    title: str | None
    raw_text: str
    cleaned_text: str | None
    emotional_tone: list[str] | None
    lucid: bool
    recurring: bool
    notes: str | None
    day_residue: str | None
    recorded_at: datetime
    symbols: list[SymbolOut] = []
    interpretation: InterpretationOut | None = None


# ── Search ─────────────────────────────────────────────────────────────────────

class DreamSearchResult(BaseModel):
    chunk_id: str
    dream_id: str
    dreamed_on: date
    title: str | None
    source_type: str
    text: str
    similarity: float


class DreamSearchResponse(BaseModel):
    query: str
    results: list[DreamSearchResult]


# ── Chunks ────────────────────────────────────────────────────────────────────

class DreamChunkDetail(BaseModel):
    chunk_id: str
    chunk_index: int
    dream_id: str
    dream_title: str | None
    dreamed_on: date
    source_type: str
    text: str
    prev_chunk_id: str | None
    next_chunk_id: str | None


# ── Symbols ────────────────────────────────────────────────────────────────────

class ArchetypeSummary(BaseModel):
    archetype: str
    count: int
    dream_ids: list[str]
