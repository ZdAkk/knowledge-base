import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { dreamsApi } from "@/api/dreams";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";

function formatSourceType(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Loader() {
  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">
      <Skeleton className="h-3 w-64" />
      <Skeleton className="h-6 w-48" />
      <Separator />
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}

export function DreamChunkPage() {
  const { dreamId, chunkId } = useParams<{ dreamId: string; chunkId: string }>();

  const { data: chunk, isLoading, error } = useQuery({
    queryKey: ["dream-chunk", dreamId, chunkId],
    queryFn: () => dreamsApi.chunk(dreamId!, chunkId!),
    enabled: !!dreamId && !!chunkId,
  });

  return (
    <div>
      {/* Top bar */}
      <div className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur-sm px-6 py-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={`/dreams/${dreamId}`} className="flex items-center gap-1.5 text-muted-foreground">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to dream
          </Link>
        </Button>
      </div>

      {isLoading && <Loader />}

      {error && (
        <div className="max-w-2xl mx-auto px-6 py-10">
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            Failed to load chunk.
          </div>
        </div>
      )}

      {chunk && (
        <article className="max-w-2xl mx-auto px-6 py-8 space-y-6">
          {/* Breadcrumb */}
          <Breadcrumb
            items={[
              { label: "Dreams", href: "/dreams" },
              {
                label: chunk.dream_title ?? formatDate(chunk.dreamed_on),
                href: `/dreams/${chunk.dream_id}`,
              },
              {
                label: formatSourceType(chunk.source_type),
                href: `/dreams/${chunk.dream_id}`,
              },
              { label: `Chunk #${chunk.chunk_index + 1}` },
            ]}
          />

          {/* Meta */}
          <div>
            <p className="text-xs text-muted-foreground font-mono">
              {formatSourceType(chunk.source_type)} · chunk {chunk.chunk_index + 1}
            </p>
          </div>

          <Separator />

          {/* Text */}
          <div className="dream-prose">
            {chunk.text.split("\n\n").map((para, i) => (
              <p key={i}>{para.trim()}</p>
            ))}
          </div>

          <Separator />

          {/* Prev / Next */}
          <div className="flex items-center justify-between">
            {chunk.prev_chunk_id ? (
              <Button variant="outline" size="sm" asChild>
                <Link to={`/dreams/${chunk.dream_id}/chunks/${chunk.prev_chunk_id}`}>
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Previous chunk
                </Link>
              </Button>
            ) : (
              <div />
            )}
            {chunk.next_chunk_id ? (
              <Button variant="outline" size="sm" asChild>
                <Link to={`/dreams/${chunk.dream_id}/chunks/${chunk.next_chunk_id}`}>
                  Next chunk
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </Button>
            ) : (
              <div />
            )}
          </div>
        </article>
      )}
    </div>
  );
}
