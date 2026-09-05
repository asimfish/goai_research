import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 构建产物由 tools/console_server.py 托管在同源根路径；开发时把 /api 代理到本地后端。
export default defineConfig({
  plugins: [vue()],
  base: './',
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 1500 },
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.GOAI_CONSOLE_API || 'http://127.0.0.1:5051', changeOrigin: true } },
  },
})
