import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { dreamsApi } from "@/api/dreams";
import { DreamDetail } from "@/components/dreams/DreamDetail";
import { DreamDetailLoader } from "@/components/shared/PageLoader";
import { Button } from "@/components/ui/button";

export function DreamDetailPage() {
  const { dreamId } = useParams<{ dreamId: string }>();

  const { data: dream, isLoading, error } = useQuery({
    queryKey: ["dream", dreamId],
    queryFn: () => dreamsApi.get(dreamId!),
    enabled: !!dreamId,
  });

  return (
    <div>
      {/* Top bar */}
      <div className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur-sm px-6 py-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/dreams" className="flex items-center gap-1.5 text-muted-foreground">
            <ArrowLeft className="w-3.5 h-3.5" />
            All dreams
          </Link>
        </Button>
      </div>

      {/* Content */}
      {isLoading && <DreamDetailLoader />}

      {error && (
        <div className="max-w-2xl mx-auto px-6 py-10">
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            Failed to load this dream.
          </div>
        </div>
      )}

      {dream && <DreamDetail dream={dream} />}
    </div>
  );
}
