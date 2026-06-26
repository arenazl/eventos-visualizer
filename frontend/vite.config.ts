import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5175,
    cors: true,
    // Dev proxy: en dev, /api y /auth caen al backend local (mismo patron same-origin que prod).
    // En prod lo resuelve el proxy de Netlify (public/_redirects). VITE_API_URL ya no se usa.
    proxy: {
      '/api': { target: 'http://localhost:8002', changeOrigin: true },
      '/auth': { target: 'http://localhost:8002', changeOrigin: true }
    },
    // Better hot reload and cache handling
    hmr: {
      overlay: false // Disable error overlay that can cause issues
    },
    fs: {
      strict: false // Allow serving files from outside root
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  // Optimize dependencies to prevent reload issues
  optimizeDeps: {
    include: ['react', 'react-dom', 'zustand']
  },
  // Clear cache on startup
  cacheDir: 'node_modules/.vite'
})