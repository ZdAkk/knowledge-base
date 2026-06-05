import { Badge } from "@/components/ui/badge";
import type { DreamSymbol } from "@/types";

interface Props {
  symbol: DreamSymbol;
}

export function SymbolCard({ symbol }: Props) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2.5">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-foreground">{symbol.name}</h4>
        {symbol.archetype && (
          <Badge variant="amber" className="shrink-0 text-xs">
            {symbol.archetype}
          </Badge>
        )}
      </div>

      {symbol.description && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          {symbol.description}
        </p>
      )}

      {symbol.significance && (
        <p className="text-xs text-foreground/80 leading-relaxed border-t border-border pt-2">
          {symbol.significance}
        </p>
      )}

      {symbol.jungian_concept && (
        <Badge variant="outline" className="text-xs">
          {symbol.jungian_concept}
        </Badge>
      )}
    </div>
  );
}
