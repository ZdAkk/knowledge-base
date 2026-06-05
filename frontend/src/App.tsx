import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Shell } from "@/components/layout/Shell";
import { DreamsPage } from "@/pages/DreamsPage";
import { DreamDetailPage } from "@/pages/DreamDetailPage";
import { BooksPage } from "@/pages/BooksPage";
import { BookDetailPage } from "@/pages/BookDetailPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Shell />}>
            <Route index element={<Navigate to="/dreams" replace />} />
            <Route path="dreams" element={<DreamsPage />} />
            <Route path="dreams/:dreamId" element={<DreamDetailPage />} />
            <Route path="books" element={<BooksPage />} />
            <Route path="books/:slug" element={<BookDetailPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
