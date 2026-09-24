import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/tasks': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/tests': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/student': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/collab': {
        target: 'ws://realtime:1234',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/collab/, ''),
      },
    },
  },
})
