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

// 移动端判定（与 HomeView 的切换阈值保持一致，另加 UA 兜底平板）
const isMobileDevice = () =>
  window.matchMedia('(max-width: 768px)').matches ||
  /Android|iPhone|iPad|Mobi/i.test(navigator.userAgent);

// AI 类接口耗时 30~60 秒（后端 LLM httpx timeout=60s），不能用短超时
const LONG_TIMEOUT_PATHS = [
  /^\/recommend/,   // AI 推荐 + 打包清单
  /^\/tryon/,       // 虚拟试穿（生图）
  /^\/items$/,      // 上传衣物（VL 识别）
  /^\/closet\/search/, // 向量语义搜索
  /^\/api\/chat/,   // AI 对话
  /^\/weather/,     // 高德天气
];
const DEFAULT_TIMEOUT = 15000;
const LONG_TIMEOUT = 180000;

// 全局 fetch 拦截器：自动附加 token + 游客头 + 统一错误处理 + 分级超时保护
const originalFetch = window.fetch
window.fetch = (input, init = {}) => {
  const token = localStorage.getItem('auth_token') || ''
  const headers = new Headers(init.headers || {})
  if (token) {
    headers.set('Authorization', token)
  }
  // 游客试玩模式：无登录时附加 X-Guest 头，后端识别为演示账号
  if (!token && localStorage.getItem('guest_mode') === '1') {
    headers.set('X-Guest', '1')
  }

  // 组件自带 signal 时由组件自己控制超时（如试穿页的 180s），这里不再叠加
  let timer = null
  let signal = init.signal
  if (!signal) {
    const pathname = new URL(
      typeof input === 'string' ? input : (input && input.url) || '',
      window.location.href
    ).pathname
    const timeout = LONG_TIMEOUT_PATHS.some(re => re.test(pathname))
      ? LONG_TIMEOUT
      : DEFAULT_TIMEOUT
    const controller = new AbortController()
    timer = setTimeout(() => controller.abort(), timeout)
    signal = controller.signal
  }

  return originalFetch(input, { ...init, headers, signal }).then(async res => {
    // 401: token 过期或无效
    // 移动端：清 token 后自动以游客身份重新进入，保持演示流畅；
    // 桌面端：跳转登录页（只跳转一次，避免死循环）
    if (res.status === 401) {
      if (isMobileDevice()) {
        if (!window.__guestReentering) {
          window.__guestReentering = true
          console.warn('[Auth] 移动端 token 无效，自动切换为游客模式')
          localStorage.removeItem('auth_token')
          localStorage.setItem('guest_mode', '1')
          window.location.reload()
        }
      } else if (window.location.pathname !== '/login') {
        console.warn('[Auth] Token 无效，即将跳转到登录页')
        localStorage.removeItem('auth_token') // 清除无效 token
        router.push('/login')
      }
    }
    // 500+: 服务器错误 → 不阻断，让各组件自己处理
    if (res.status >= 500) {
      console.error(`[API Error] ${input} → ${res.status}`)
    }
    return res
  }).finally(() => {
    if (timer) clearTimeout(timer)
  })
}
