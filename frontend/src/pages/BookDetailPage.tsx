import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, Hash } from "lucide-react";
import { booksApi } from "@/api/books";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground/60 mb-4">
      {children}
    </p>
  );
}

function Loader() {
  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-8">
      <Skeleton className="h-4 w-20" />
      <div className="space-y-2">
        <Skeleton className="h-7 w-80" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-14 rounded-lg" />
        ))}
      </div>
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export function BookDetailPage() {
  const { slug } = useParams<{ slug: string }>();

  const { data: book, isLoading, error } = useQuery({
    queryKey: ["book", slug],
    queryFn: () => booksApi.get(slug!),
    enabled: !!slug,
  });

  return (
    <div>
      {/* Top bar */}
      <div className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur-sm px-6 py-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/books" className="flex items-center gap-1.5 text-muted-foreground">
            <ArrowLeft className="w-3.5 h-3.5" />
            All books
          </Link>
        </Button>
      </div>

      {isLoading && <Loader />}

      {error && (
        <div className="max-w-2xl mx-auto px-6 py-10">
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            Failed to load this book.
          </div>
        </div>
      )}

      {book && (
        <article className="max-w-2xl mx-auto px-6 py-10 space-y-8">

          {/* Header */}
          <header className="space-y-2">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                <BookOpen className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-medium text-foreground leading-snug">
                  {book.title ?? book.book_slug}
                </h1>
                {book.author && (
                  <p className="text-sm text-muted-foreground mt-0.5">{book.author}</p>
                )}
              </div>
            </div>
          </header>

          <Separator />

          {/* Metadata grid */}
          <section>
            <SectionLabel>Details</SectionLabel>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Publisher", value: book.publisher },
                { label: "Language", value: book.language?.toUpperCase() },
                { label: "ISBN", value: book.isbn?.replace(/^urn:isbn:/i, "") },
                { label: "Indexed", value: book.extracted_at ? formatDateTime(book.extracted_at) : null },
              ]
                .filter((item) => item.value)
                .map(({ label, value }) => (
                  <div
                    key={label}
                    className="rounded-lg border border-border bg-muted/30 px-4 py-3"
                  >
                    <p className="text-xs text-muted-foreground mb-1">{label}</p>
                    <p className="text-sm text-foreground">{value}</p>
                  </div>
                ))}
            </div>
          </section>

          {/* Embedding status */}
          <section>
            <SectionLabel>Embedding Status</SectionLabel>
            <div className="flex items-center gap-3">
              <Badge
                variant={book.embedded_chunks === book.total_chunks ? "emerald" : "amber"}
              >
                {book.embedded_chunks === book.total_chunks
                  ? `✓ All ${book.total_chunks} chunks embedded`
                  : `${book.embedded_chunks} / ${book.total_chunks} chunks embedded`}
              </Badge>
            </div>
          </section>

          <Separator />

          {/* Chapters */}
          {book.chapters.length > 0 && (
            <section>
              <SectionLabel>
                Chapters — {book.chapters.length} section{book.chapters.length !== 1 ? "s" : ""}
              </SectionLabel>
              <div className="space-y-1.5">
                {book.chapters.map((ch) => (
                  <div
                    key={ch.chapter_order}
                    className="flex items-center justify-between px-4 py-2.5 rounded-md bg-muted/20 border border-border/50"
                  >
                    <p className="text-sm text-foreground/80 truncate pr-4">
                      {ch.chapter_title || `Section ${ch.chapter_order + 1}`}
                    </p>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                      <Hash className="w-3 h-3" />
                      {ch.chunk_count}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </article>
      )}
    </div>
  );
}
