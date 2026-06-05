import { api } from "./client";
import type {
  DreamSummary,
  DreamDetail,
  DreamSearchResult,
  ArchetypeSummary,
} from "@/types";

export const dreamsApi = {
  list: (params?: { limit?: number; offset?: number; from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    return api.get<DreamSummary[]>(`/dreams/list?${q}`);
  },

  get: (dreamId: string) => api.get<DreamDetail>(`/dreams/${dreamId}`),

  search: (params: {
    q: string;
    limit?: number;
    threshold?: number;
    source_type?: string;
  }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.limit) q.set("limit", String(params.limit));
    if (params.threshold) q.set("threshold", String(params.threshold));
    if (params.source_type) q.set("source_type", params.source_type);
    return api.get<{ query: string; results: DreamSearchResult[] }>(
      `/dreams/search?${q}`
    );
  },

  archetypes: () => api.get<ArchetypeSummary[]>("/dreams/symbols"),

  delete: (dreamId: string) => api.delete<{ dream_id: string; message: string }>(`/dreams/${dreamId}`),
};
