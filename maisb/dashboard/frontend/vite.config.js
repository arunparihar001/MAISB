import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev mode proxy /api → backend on localhost:8000.
// In Docker the nginx conf handles /api → backend service.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
