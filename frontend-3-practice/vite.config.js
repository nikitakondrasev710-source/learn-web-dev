// vite.config.js
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 3000,
  },
  root: ".",
  // Проект не использует PostCSS. Без этой настройки Vite поднимается
  // вверх по дереву и подхватывает посторонний postcss.config.mjs
  // из родительской папки — сборка падает с «Invalid PostCSS Plugin».
  css: {
    postcss: { plugins: [] },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
  },
});
