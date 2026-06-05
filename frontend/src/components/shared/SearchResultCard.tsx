import { Link } from "react-router-dom";
import { BookOpen, Moon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { UnifiedSearchResult } from "@/types";

interface Props {
  result: UnifiedSearchResult;
}

function SimilarityBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary/60 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground tabular-nums w-8 text-right">
        {pct}%
      </span>
    </div>
  );
}

function chunkUrl(result: UnifiedSearchResult): string {
  if (result.source_type === "book") {
    return `/books/${result.source_id}/chunks/${result.chunk_id}`;
  }
  return `/dreams/${result.source_id}/chunks/${result.chunk_id}`;
}

function formatContext(context: string | null, sourceType: "book" | "dream"): string {
  if (!context) return "";
  if (sourceType === "dream") {
    // source_type values: cleaned_dream, jungian_analysis, waking_life
    return context.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return context;
}

export function SearchResultCard({ result }: Props) {
  const isBook = result.source_type === "book";
  const excerpt = result.text.length > 320
    ? result.text.slice(0, 320).trimEnd() + "…"
    : result.text;

  return (
    <Link to={chunkUrl(result)}>
      <Card className="hover:border-border/80 hover:bg-card/80 transition-all duration-150 cursor-pointer group">
        <CardContent className="p-4 space-y-3">
          {/* Header row */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <Badge variant={isBook ? "amber" : "violet"} className="flex items-center gap-1 shrink-0">
                {isBook ? <BookOpen className="w-3 h-3" /> : <Moon className="w-3 h-3" />}
                {isBook ? "Book" : "Dream"}
              </Badge>
              <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                {result.title ?? result.source_id}
              </p>
            </div>
          </div>

          {/* Context */}
          {result.context && (
            <p className="text-xs text-muted-foreground">
              {formatContext(result.context, result.source_type)}
            </p>
          )}

          {/* Text excerpt */}
          <p className="text-sm text-foreground/75 leading-relaxed font-serif">
            {excerpt}
          </p>

          {/* Similarity bar */}
          <SimilarityBar value={result.similarity} />
        </CardContent>
      </Card>
    </Link>
  );
}
