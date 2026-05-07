import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 教育智能客服调试页：/api 走 edu-service-backend（默认 8012）
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8012',
        changeOrigin: true,
      },
      '/edu': {
        target: 'http://127.0.0.1:9001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/edu/, ''),
      },
    },
  },
})
