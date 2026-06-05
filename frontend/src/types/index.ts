// ── Dreams ────────────────────────────────────────────────────────────────────

export interface DreamSummary {
  dream_id: string;
  dreamed_on: string;
  title: string | null;
  emotional_tone: string[] | null;
  lucid: boolean;
  has_interpretation: boolean;
  recorded_at: string;
}

export interface DreamSymbol {
  symbol_id: string;
  name: string;
  archetype: string | null;
  description: string | null;
  significance: string | null;
  jungian_concept: string | null;
}

export interface DreamInterpretation {
  interpretation_id: string;
  central_theme: string | null;
  jungian_analysis: string | null;
  waking_life: string | null;
  message: string | null;
  books_used: string[] | null;
  web_sources: string[] | null;
  scholar_sources: string[] | null;
  model_used: string | null;
  generated_at: string;
}

export interface DreamDetail {
  dream_id: string;
  dreamed_on: string;
  title: string | null;
  raw_text: string;
  cleaned_text: string | null;
  emotional_tone: string[] | null;
  lucid: boolean;
  recurring: boolean;
  notes: string | null;
  day_residue: string | null;
  recorded_at: string;
  symbols: DreamSymbol[];
  interpretation: DreamInterpretation | null;
}

export interface DreamSearchResult {
  chunk_id: string;
  dream_id: string;
  dreamed_on: string;
  title: string | null;
  source_type: string;
  text: string;
  similarity: number;
}

export interface ArchetypeSummary {
  archetype: string;
  count: number;
  dream_ids: string[];
}

// ── Books ─────────────────────────────────────────────────────────────────────

export interface BookSummary {
  book_slug: string;
  title: string;
  author: string | null;
  total_chunks: number;
  embedded_chunks: number;
  extracted_at: string;
}

export interface BookChapter {
  chapter_title: string | null;
  chapter_order: number;
  chunk_count: number;
}

export interface BookChunkItem {
  chunk_id: string;
  chunk_index: number;
  chapter_title: string | null;
  chapter_order: number;
  approx_tokens: number;
  text: string;
}

export interface BookChunkDetail {
  chunk_id: string;
  chunk_index: number;
  book_slug: string;
  book_title: string | null;
  book_author: string | null;
  chapter_title: string | null;
  chapter_order: number;
  approx_tokens: number;
  text: string;
  prev_chunk_id: string | null;
  next_chunk_id: string | null;
}

export interface DreamChunkDetail {
  chunk_id: string;
  chunk_index: number;
  dream_id: string;
  dream_title: string | null;
  dreamed_on: string;
  source_type: string;
  text: string;
  prev_chunk_id: string | null;
  next_chunk_id: string | null;
}

export interface UnifiedSearchResult {
  chunk_id: string;
  source_type: "book" | "dream";
  source_id: string;
  title: string | null;
  context: string | null;
  text: string;
  similarity: number;
}

export interface UnifiedSearchResponse {
  query: string;
  results: UnifiedSearchResult[];
}

export interface BookDetail {
  book_slug: string;
  title: string | null;
  author: string | null;
  language: string | null;
  publisher: string | null;
  isbn: string | null;
  extracted_at: string | null;
  total_chunks: number;
  embedded_chunks: number;
  chapters: BookChapter[];
}
