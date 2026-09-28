import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
const backendTarget = process.env.VITE_BACKEND_PROXY_TARGET ?? 'http://host.docker.internal:8000'
const realtimeTarget = process.env.VITE_REALTIME_PROXY_TARGET ?? 'ws://host.docker.internal:1234'
// https://vite.dev/config/
export default defineConfig({
  cacheDir: '.vite-cache',
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/collab': {
        target: realtimeTarget,
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/collab/, ''),
      },
    },
  },
})
