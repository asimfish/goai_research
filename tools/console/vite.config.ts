import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const openlab = new URL('../../../goai_final_lab/src/OpenLabSite/src', import.meta.url).pathname
export default defineConfig({
  plugins: [vue()],
  base: './',
  resolve: { alias: { '@materials': openlab }, dedupe: ['vue', 'pinia', 'vue-router', 'naive-ui'] },
  define: { __OPENLAB_DEV_PROXY_TARGET__: JSON.stringify('') },
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 1500 },
  server: {
    port: 5173,
    fs: { allow: ['../../..', openlab] },
    proxy: {
      '/api': { target: process.env.GOAI_CONSOLE_API || 'http://127.0.0.1:5051', changeOrigin: true },
      '/edge': { target: process.env.OPENLAB_EDGE_PROXY_TARGET || 'http://127.0.0.1:8002', changeOrigin: true, ws: true, rewrite: p => p.replace(/^\/edge/, '') },
      '/execution': { target: 'http://127.0.0.1:8093' },
      '/sim': { target: 'http://127.0.0.1:8093', ws: true },
    },
  },
})
