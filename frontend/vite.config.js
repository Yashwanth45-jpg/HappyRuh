import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Listen on all network interfaces (fixes IPv6 issue)
    port: 5173,
    strictPort: false,  // Auto-increment if port is busy
    proxy: {
      // Proxy dev requests to backend
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false
      }
    }
  }
});
