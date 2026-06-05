import { Badge } from "@/components/ui/badge";
import type { BadgeProps } from "@/components/ui/badge";

const toneColors: Record<string, BadgeProps["variant"]> = {
  fear: "rose",
  anxiety: "rose",
  dread: "rose",
  terror: "rose",
  accomplishment: "emerald",
  triumph: "emerald",
  joy: "amber",
  elation: "amber",
  happiness: "amber",
  sadness: "blue",
  grief: "blue",
  melancholy: "blue",
  confusion: "violet",
  disorientation: "violet",
  awe: "violet",
  wonder: "violet",
  anger: "rose",
  frustration: "rose",
  curiosity: "blue",
  peace: "emerald",
  calm: "emerald",
};

function getToneVariant(tone: string): BadgeProps["variant"] {
  const lower = tone.toLowerCase();
  return toneColors[lower] ?? "muted";
}

interface Props {
  tone: string;
}

export function ToneBadge({ tone }: Props) {
  return (
    <Badge variant={getToneVariant(tone)} className="capitalize">
      {tone}
    </Badge>
  );
}
