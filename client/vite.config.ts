import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The Pipecat runner serves /start and /sessions/{id}/api/offer. The client calls
// them under /api so a single proxy rule covers both and no CORS setup is needed.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:7860",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
