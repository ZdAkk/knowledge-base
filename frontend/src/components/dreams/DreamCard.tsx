import { Link } from "react-router-dom";
import { Eye, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ToneBadge } from "./ToneBadge";
import { formatDate } from "@/lib/utils";
import type { DreamSummary } from "@/types";

interface Props {
  dream: DreamSummary;
}

export function DreamCard({ dream }: Props) {
  return (
    <Link to={`/dreams/${dream.dream_id}`}>
      <Card className="hover:border-border/80 hover:bg-card/80 transition-all duration-150 cursor-pointer group">
        <CardContent className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {/* Date */}
              <p className="text-xs text-muted-foreground mb-1.5 font-mono">
                {formatDate(dream.dreamed_on)}
              </p>

              {/* Title */}
              <h3 className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                {dream.title ?? "Untitled dream"}
              </h3>
            </div>

            {/* Status */}
            <div className="shrink-0 flex items-center gap-1.5">
              {dream.has_interpretation ? (
                <div className="flex items-center gap-1 text-xs text-primary/70">
                  <Sparkles className="w-3 h-3" />
                </div>
              ) : (
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500/40" />
              )}
            </div>
          </div>

          {/* Badges */}
          {(dream.emotional_tone?.length || dream.lucid) && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {dream.emotional_tone?.map((tone) => (
                <ToneBadge key={tone} tone={tone} />
              ))}
              {dream.lucid && (
                <Badge variant="violet" className="flex items-center gap-1">
                  <Eye className="w-2.5 h-2.5" />
                  Lucid
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
