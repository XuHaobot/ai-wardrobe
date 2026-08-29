// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
    // 游客试玩模式：首页无需强制登录，未登录可体验演示衣橱
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  // 更多路由以后添加
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  const guest = localStorage.getItem('guest_mode') === '1'
  // 已登录 或 游客模式 均可进入首页
  if (to.name !== 'Login' && !token && !guest) {
    const isMobile =
      window.matchMedia('(max-width: 768px)').matches ||
      /Android|iPhone|iPad|Mobi/i.test(navigator.userAgent)
    if (isMobile) {
      // 移动端：首次打开直接以游客身份进入演示衣橱（不再跳桌面版登录页）
      localStorage.setItem('guest_mode', '1')
      next()
    } else {
      next({ name: 'Login' })
    }
  } else {
    next()
  }
})

export default router
