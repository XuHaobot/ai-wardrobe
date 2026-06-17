// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

// 引入 Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)

app.use(router)
app.use(ElementPlus)

// 全局错误处理 —— 防止组件崩溃导致白屏
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err, info);
  // 不弹窗打扰用户，只在控制台记录
};

app.mount('#app')

// 全局 fetch 拦截器：自动附加 token + 统一错误处理 + 10秒超时保护
const originalFetch = window.fetch
window.fetch = (input, init = {}) => {
  const token = localStorage.getItem('auth_token') || ''
  const headers = new Headers(init.headers || {})
  if (token) {
    headers.set('Authorization', token)
  }
  // 默认10秒超时（可通过 init.signal 自定义覆盖）
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)
  const signal = init.signal || controller.signal
  return originalFetch(input, { ...init, headers, signal }).then(async res => {
    // 401: token 过期或无效 → 跳转登录（只跳转一次，避免死循环）
    if (res.status === 401 && window.location.pathname !== '/login') {
      console.warn('[Auth] Token 无效，即将跳转到登录页')
      localStorage.removeItem('auth_token') // 清除无效 token
      router.push('/login')
    }
    // 500+: 服务器错误 → 不阻断，让各组件自己处理
    if (res.status >= 500) {
      console.error(`[API Error] ${input} → ${res.status}`)
    }
    return res
  }).finally(() => {
    clearTimeout(timer)
  })
}
