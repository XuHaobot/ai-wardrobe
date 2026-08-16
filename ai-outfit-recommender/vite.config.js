import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/recommend': {
        target: backendTarget,
        changeOrigin: true,
        timeout: 120000,
        proxyTimeout: 120000,
      },
      '/items': {
        target: backendTarget,
        changeOrigin: true,
        timeout: 120000,
        proxyTimeout: 120000,
      },
      '/closet': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        timeout: 120000,
        proxyTimeout: 120000,
      },
      '/uploads': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/auth': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/users': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/user': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/weather': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/tryon': {
        target: backendTarget,
        changeOrigin: true,
        timeout: 120000,
        proxyTimeout: 120000,
      }
    }
  }
})
