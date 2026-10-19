import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const django = 'http://127.0.0.1:8000'

// The build lands in the Django app's static tree so `runserver` (dev) and
// `collectstatic` (deploy) both serve it. The Vite dev server proxies the
// Django routes instead, so the client always uses same-origin paths.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Production assets live under Django static; the dev server keeps the
  // client at `/` so URL-state paths match the Django-served screen.
  base: command === 'build' ? '/static/crm/dist/' : '/',
  build: {
    outDir: '../crm/static/crm/dist',
    emptyOutDir: true,
    manifest: true,
    // Django owns the HTML shell; build the module entry only so no
    // dist/index.html is emitted and the manifest key is stable.
    rollupOptions: { input: 'src/main.tsx' },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: django, changeOrigin: true },
      '/export': { target: django, changeOrigin: true },
      '/static': { target: django, changeOrigin: true },
    },
  },
}))
