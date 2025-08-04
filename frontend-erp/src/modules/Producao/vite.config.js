import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const buildTimestamp = Date.now();
// Base path for deploying under /producao
const basePath = '/producao/';
export default defineConfig({
  base: basePath,
  plugins: [
    react(),
    // inject a timestamp query to the main script to bust browser cache on each build
    {
      name: 'inject-timestamp',
      transformIndexHtml(html) {
        // Inject versioned script path under basePath to bust cache
        return html.replace(
          /<script type="module" src="\/src\/main\.jsx"><\/script>/,
          `<script type="module" src="${basePath}src/main.jsx?t=${buildTimestamp}"></script>`
        );
      }
    }
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
})
