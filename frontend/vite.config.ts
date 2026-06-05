import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Dev proxy: forwards /api/* to the real API with auth header
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET ?? "http://192.168.178.40:9200",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
        headers: process.env.VITE_API_TOKEN
          ? { Authorization: `Bearer ${process.env.VITE_API_TOKEN}` }
          : {},
      },
    },
  },
});
