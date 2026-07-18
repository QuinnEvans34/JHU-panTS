import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Static-first: the app just serves files from public/cases/. No backend.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, open: true },
})
