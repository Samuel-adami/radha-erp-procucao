import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Isso configura o alias '@' para apontar para o diretório 'src'
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3015, // Define a porta do servidor de desenvolvimento para 3015
    host: '0.0.0.0' // Adiciona esta linha para bind em todas as interfaces
  }
})