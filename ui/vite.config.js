import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Static-first: the app just serves files from public/cases/. No backend.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, open: true },
  build: {
    // Sites registers static files from the conventional client directory.
    // Keeping the Worker entry beside it lets the same bundle run locally
    // with `vite preview` and in the hosted Cloudflare environment.
    outDir: 'dist/client',
  },
})
