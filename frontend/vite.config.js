import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // /api 로 시작하는 요청은 FastAPI 서버로 전달
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
