import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Em desenvolvimento, /api é encaminhado para o backend (uvicorn na porta 8000).
// Em produção, defina VITE_API_BASE (ex.: https://sua-api.exemplo.com/api) no build.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
