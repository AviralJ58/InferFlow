import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Proxy API requests to the chat service during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy monitoring requests to the monitoring service
      '/monitoring': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/monitoring/, ''),
      },
    },
  },
})
