import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const DIRECCION_BACKEND = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Permite abrirlo desde una tablet en la misma red Wi-Fi.
    port: 5173,
    proxy: {
      "/api": DIRECCION_BACKEND,
      "/ws": { target: DIRECCION_BACKEND, ws: true },
    },
  },
});
