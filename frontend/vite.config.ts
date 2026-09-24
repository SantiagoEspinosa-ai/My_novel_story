/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// PLAN-22 DP-3: la web de verdad se sirve con Vite y su proxy manda /api a uvicorn.
// El backend no declara origen (SPEC-22 DA-3), asi que el navegador nunca lo llama
// directo: todo va por /api, y el proxy quita el prefijo.
const BACKEND = process.env.HARNESS_API ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    proxy: {
      "/api": { target: BACKEND, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
});
