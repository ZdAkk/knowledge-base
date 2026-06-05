import { api } from "./client";
import type { BookSummary, BookDetail, BookChunkItem, BookChunkDetail } from "@/types";

export const booksApi = {
  list: () => api.get<BookSummary[]>("/books/list"),

  get: (slug: string) => api.get<BookDetail>(`/books/${slug}`),

  chunks: (slug: string, chapterOrder?: number, limit = 100) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (chapterOrder !== undefined) q.set("chapter_order", String(chapterOrder));
    return api.get<BookChunkItem[]>(`/books/${slug}/chunks?${q}`);
  },

  chunk: (slug: string, chunkId: string) =>
    api.get<BookChunkDetail>(`/books/${slug}/chunks/${chunkId}`),

  search: (params: { q: string; limit?: number; threshold?: number }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.limit) q.set("limit", String(params.limit));
    if (params.threshold) q.set("threshold", String(params.threshold));
    return api.get<{ query: string; results: unknown[] }>(`/books/search?${q}`);
  },
};
