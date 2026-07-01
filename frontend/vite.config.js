import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/admin/api': 'http://localhost:8004',
      '/v1': 'http://localhost:8000',
      '/gateway/admin': 'http://localhost:8000',
    }
  }
})
