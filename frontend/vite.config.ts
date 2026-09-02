import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Proxying /api means the browser only ever talks to one origin, so the session
    // cookie is same-site by construction and CORS never enters the picture in
    // development. The backend still sets CORS headers for anyone running the two
    // servers on separate ports without the proxy.
    proxy: {
      "/api": {
        target: process.env.API_PROXY_TARGET ?? "http://api:8000",
        changeOrigin: true,
      },
    },
    // File change events do not cross the Docker bind mount reliably on Windows
    // hosts, and hot reload silently stops working without polling.
    watch: { usePolling: true },
  },
});
