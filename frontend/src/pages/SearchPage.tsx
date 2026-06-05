import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { searchApi } from "@/api/search";
import { SearchResultCard } from "@/components/shared/SearchResultCard";
import { Slider } from "@/components/ui/slider";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";

const LIMIT_OPTIONS = [5, 10, 20, 50] as const;
type Source = "books" | "dreams";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sources, setSources] = useState<Set<Source>>(new Set(["books", "dreams"]));
  const [threshold, setThreshold] = useState(0.3);
  const [limit, setLimit] = useState<number>(10);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["search", submitted, Array.from(sources).sort().join(","), threshold, limit],
    queryFn: () =>
      searchApi.search({
        q: submitted,
        sources: Array.from(sources).join(","),
        threshold,
        limit,
      }),
    enabled: submitted.trim().length > 0,
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) setSubmitted(query.trim());
    },
    [query]
  );

  const toggleSource = (s: Source) => {
    setSources((prev) => {
      const next = new Set(prev);
      if (next.has(s) && next.size > 1) next.delete(s);
      else next.add(s);
      return next;
    });
  };

  const loading = isLoading || isFetching;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-lg font-medium text-foreground">Search</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Semantic search across your entire knowledge base
        </p>
      </div>

      {/* Search input */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search anything…"
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border bg-card text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </form>

      {/* Filters */}
      <div className="mb-6 p-4 rounded-lg border border-border bg-card/50 space-y-4">
        {/* Sources */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground w-20 shrink-0">Sources</span>
          <div className="flex gap-2">
            {(["books", "dreams"] as Source[]).map((s) => (
              <button
                key={s}
                onClick={() => toggleSource(s)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                  sources.has(s)
                    ? s === "books"
                      ? "border-amber-500/50 bg-amber-500/10 text-amber-400"
                      : "border-violet-500/50 bg-violet-500/10 text-violet-400"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Threshold */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground w-20 shrink-0">
            Min similarity
          </span>
          <div className="flex-1 flex items-center gap-3">
            <Slider
              min={0.1}
              max={0.9}
              step={0.05}
              value={[threshold]}
              onValueChange={([v]) => setThreshold(v)}
              className="flex-1"
            />
            <span className="text-xs text-muted-foreground tabular-nums w-8">
              {Math.round(threshold * 100)}%
            </span>
          </div>
        </div>

        {/* Limit */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground w-20 shrink-0">Results</span>
          <div className="flex gap-1.5">
            {LIMIT_OPTIONS.map((n) => (
              <button
                key={n}
                onClick={() => setLimit(n)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors border ${
                  limit === n
                    ? "border-primary/50 bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {loading && submitted && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-lg" />
          ))}
        </div>
      )}

      {!loading && data && data.results.length === 0 && (
        <EmptyState
          icon={Search}
          title="No results found"
          description="Try lowering the similarity threshold or broadening your query."
        />
      )}

      {!loading && data && data.results.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground mb-3">
            {data.results.length} result{data.results.length !== 1 ? "s" : ""} for "{data.query}"
          </p>
          {data.results.map((result) => (
            <SearchResultCard key={result.chunk_id} result={result} />
          ))}
        </div>
      )}

      {!submitted && (
        <div className="py-16 text-center">
          <p className="text-sm text-muted-foreground">
            Enter a query above and press Enter
          </p>
        </div>
      )}
    </div>
  );
}
