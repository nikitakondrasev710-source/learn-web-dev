import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import apiMiddleware from "./server/server.js";

export default defineConfig({
  plugins: [react(), apiMiddleware()],
  server: {
    port: 3000,
  },
  // Проект не использует PostCSS. Без этой настройки Vite поднимается
  // вверх по дереву и подхватывает посторонний postcss.config.mjs
  // из родительской папки — сборка падает с «Invalid PostCSS Plugin».
  css: {
    postcss: { plugins: [] },
  },
});
