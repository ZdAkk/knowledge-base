import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";

interface Props {
  cleanedText: string | null;
  rawText: string;
}

function TextBlock({ text }: { text: string }) {
  return (
    <div className="dream-prose">
      {text.split("\n\n").map((para, i) => (
        <p key={i}>{para.trim()}</p>
      ))}
    </div>
  );
}

export function DreamNarrative({ cleanedText, rawText }: Props) {
  const [rawOpen, setRawOpen] = useState(false);
  const primary = cleanedText ?? rawText;
  const hasRaw = !!cleanedText && cleanedText !== rawText;

  return (
    <div className="space-y-4">
      <TextBlock text={primary} />

      {hasRaw && (
        <Collapsible open={rawOpen} onOpenChange={setRawOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="sm" className="text-muted-foreground gap-1.5 -ml-2">
              {rawOpen ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
              {rawOpen ? "Hide" : "Show"} raw version
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-3 pl-4 border-l-2 border-border">
              <p className="text-xs text-muted-foreground mb-2">Original, unedited</p>
              <TextBlock text={rawText} />
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}
