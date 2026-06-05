import { api } from "./client";
import type { BookSummary } from "@/types";

export const booksApi = {
  list: () => api.get<BookSummary[]>("/books/list"),

  search: (params: { q: string; limit?: number; threshold?: number }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.limit) q.set("limit", String(params.limit));
    if (params.threshold) q.set("threshold", String(params.threshold));
    return api.get<{ query: string; results: unknown[] }>(`/books/search?${q}`);
  },
};
