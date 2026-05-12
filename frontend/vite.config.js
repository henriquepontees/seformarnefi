import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Proxy de /api/* para o servico 'backend' interno (compose e k8s).
// Permite que o codigo do front use caminhos relativos ('/api/health')
// sem precisar saber em qual porta o backend esta exposto.
export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
