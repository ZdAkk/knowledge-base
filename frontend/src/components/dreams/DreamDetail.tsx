import { Eye, RefreshCw, BookOpen, Globe, Cpu } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ToneBadge } from "./ToneBadge";
import { SymbolCard } from "./SymbolCard";
import { DreamNarrative } from "./DreamNarrative";
import { formatDate, formatDateTime } from "@/lib/utils";
import type { DreamDetail as DreamDetailType } from "@/types";

interface Props {
  dream: DreamDetailType;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground/60 mb-4">
      {children}
    </p>
  );
}

function ProseBlock({ text }: { text: string }) {
  return (
    <div className="dream-prose">
      {text.split("\n\n").map((para, i) => (
        <p key={i}>{para.trim()}</p>
      ))}
    </div>
  );
}

export function DreamDetail({ dream }: Props) {
  const { interpretation } = dream;

  return (
    <article className="max-w-2xl mx-auto px-6 py-10 space-y-10">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="space-y-3">
        <p className="text-sm text-muted-foreground font-mono">
          {formatDate(dream.dreamed_on)}
        </p>

        <h1 className="text-2xl font-medium text-foreground leading-snug">
          {dream.title ?? "Untitled Dream"}
        </h1>

        <div className="flex flex-wrap items-center gap-2">
          {dream.emotional_tone?.map((tone) => (
            <ToneBadge key={tone} tone={tone} />
          ))}
          {dream.lucid && (
            <Badge variant="violet" className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              Lucid
            </Badge>
          )}
          {dream.recurring && (
            <Badge variant="slate" className="flex items-center gap-1">
              <RefreshCw className="w-3 h-3" />
              Recurring
            </Badge>
          )}
        </div>
      </header>

      <Separator />

      {/* ── The Dream ──────────────────────────────────────────────── */}
      <section>
        <SectionLabel>The Dream</SectionLabel>
        <DreamNarrative
          cleanedText={dream.cleaned_text}
          rawText={dream.raw_text}
        />
      </section>

      {/* ── Day Residue ────────────────────────────────────────────── */}
      {dream.day_residue && (
        <>
          <Separator />
          <section>
            <SectionLabel>Day Residue</SectionLabel>
            <div className="pl-4 border-l-2 border-primary/30">
              <p className="text-sm text-muted-foreground leading-relaxed italic">
                {dream.day_residue}
              </p>
            </div>
          </section>
        </>
      )}

      {/* ── Notes ──────────────────────────────────────────────────── */}
      {dream.notes && (
        <>
          <Separator />
          <section>
            <SectionLabel>Notes</SectionLabel>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {dream.notes}
            </p>
          </section>
        </>
      )}

      {/* ── Symbols ────────────────────────────────────────────────── */}
      {dream.symbols.length > 0 && (
        <>
          <Separator />
          <section>
            <SectionLabel>Symbols & Archetypes</SectionLabel>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {dream.symbols.map((symbol) => (
                <SymbolCard key={symbol.symbol_id} symbol={symbol} />
              ))}
            </div>
          </section>
        </>
      )}

      {/* ── Interpretation ─────────────────────────────────────────── */}
      {interpretation && (
        <>
          <Separator />

          {/* Central theme */}
          {interpretation.central_theme && (
            <section>
              <SectionLabel>Central Theme</SectionLabel>
              <p className="text-base font-medium text-foreground/90 italic">
                "{interpretation.central_theme}"
              </p>
            </section>
          )}

          {/* Jungian analysis */}
          {interpretation.jungian_analysis && (
            <section>
              <SectionLabel>Jungian Analysis</SectionLabel>
              <ProseBlock text={interpretation.jungian_analysis} />
            </section>
          )}

          <Separator />

          {/* Waking life */}
          {interpretation.waking_life && (
            <section>
              <SectionLabel>Connection to Waking Life</SectionLabel>
              <ProseBlock text={interpretation.waking_life} />
            </section>
          )}

          {/* The message */}
          {interpretation.message && (
            <section>
              <SectionLabel>The Message</SectionLabel>
              <blockquote className="border-l-2 border-primary pl-5 py-1">
                <p className="text-lg font-light text-foreground/90 leading-relaxed italic font-serif">
                  {interpretation.message}
                </p>
              </blockquote>
            </section>
          )}

          <Separator />

          {/* Sources */}
          <section className="space-y-4">
            <SectionLabel>Sources</SectionLabel>

            {interpretation.books_used && interpretation.books_used.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Books</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {interpretation.books_used.map((slug) => (
                    <Badge key={slug} variant="outline" className="font-mono text-xs">
                      {slug}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {interpretation.web_sources && interpretation.web_sources.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Web</span>
                </div>
                <ul className="space-y-1">
                  {interpretation.web_sources.map((url) => (
                    <li key={url}>
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:text-primary transition-colors underline underline-offset-2 break-all"
                      >
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {interpretation.model_used && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground/50">
                <Cpu className="w-3 h-3" />
                <span>{interpretation.model_used}</span>
                <span>·</span>
                <span>{formatDateTime(interpretation.generated_at)}</span>
              </div>
            )}
          </section>
        </>
      )}

      {/* ── No interpretation yet ──────────────────────────────────── */}
      {!interpretation && (
        <>
          <Separator />
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">
              Interpretation pending — the automation hasn't processed this dream yet.
            </p>
          </div>
        </>
      )}
    </article>
  );
}
