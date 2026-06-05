import { api } from "./client";
import type { UnifiedSearchResponse } from "@/types";

export const searchApi = {
  search: (params: {
    q: string;
    sources?: string;
    threshold?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.sources) q.set("sources", params.sources);
    if (params.threshold !== undefined) q.set("threshold", String(params.threshold));
    if (params.limit !== undefined) q.set("limit", String(params.limit));
    return api.get<UnifiedSearchResponse>(`/search?${q}`);
  },
};
