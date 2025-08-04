import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const buildTimestamp = Date.now();
export default defineConfig({
  plugins: [
    react(),
    // inject a timestamp query to the main script to bust browser cache on each build
    {
      name: 'inject-timestamp',
      transformIndexHtml(html) {
        return html.replace(
          /<script type="module" src="\/src\/main\.jsx"><\/script>/,
          `<script type="module" src="/src/main.jsx?t=${buildTimestamp}"></script>`
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
