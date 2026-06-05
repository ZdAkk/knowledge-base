import { useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";
import { booksApi } from "@/api/books";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { DreamsListLoader } from "@/components/shared/PageLoader";

export function BooksPage() {
  const { data: books, isLoading, error } = useQuery({
    queryKey: ["books"],
    queryFn: () => booksApi.list(),
  });

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-lg font-medium text-foreground">Books</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {books ? `${books.length} book${books.length !== 1 ? "s" : ""} indexed` : "Knowledge library"}
        </p>
      </div>

      {isLoading && <DreamsListLoader />}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load books.
        </div>
      )}

      {books && books.length === 0 && (
        <EmptyState icon={BookOpen} title="No books indexed" />
      )}

      {books && books.length > 0 && (
        <div className="space-y-2.5">
          {books.map((book) => (
            <Card key={book.book_slug}>
              <CardContent className="p-4 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {book.title}
                  </p>
                  {book.author && (
                    <p className="text-xs text-muted-foreground mt-0.5 truncate">
                      {book.author}
                    </p>
                  )}
                </div>
                <Badge
                  variant={book.embedded_chunks === book.total_chunks ? "emerald" : "amber"}
                  className="shrink-0"
                >
                  {book.embedded_chunks === book.total_chunks
                    ? `${book.total_chunks} chunks`
                    : `${book.embedded_chunks}/${book.total_chunks}`}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
