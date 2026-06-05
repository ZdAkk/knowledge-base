import { useQuery } from "@tanstack/react-query";
import { Moon } from "lucide-react";
import { dreamsApi } from "@/api/dreams";
import { DreamCard } from "@/components/dreams/DreamCard";
import { DreamsListLoader } from "@/components/shared/PageLoader";
import { EmptyState } from "@/components/shared/EmptyState";

export function DreamsPage() {
  const { data: dreams, isLoading, error } = useQuery({
    queryKey: ["dreams"],
    queryFn: () => dreamsApi.list({ limit: 100 }),
  });

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-lg font-medium text-foreground">Dreams</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {dreams ? `${dreams.length} record${dreams.length !== 1 ? "s" : ""}` : "Dream journal"}
        </p>
      </div>

      {/* Content */}
      {isLoading && <DreamsListLoader />}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load dreams. Is the API reachable?
        </div>
      )}

      {dreams && dreams.length === 0 && (
        <EmptyState
          icon={Moon}
          title="No dreams yet"
          description="Dreams ingested through the automation will appear here."
        />
      )}

      {dreams && dreams.length > 0 && (
        <div className="space-y-2.5">
          {dreams.map((dream) => (
            <DreamCard key={dream.dream_id} dream={dream} />
          ))}
        </div>
      )}
    </div>
  );
}
