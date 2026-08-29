<template>
  <div class="m-page login-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
    </header>

    <div class="login-body">
      <div class="login-titles">
        <h1 class="login-title">Welcome Back</h1>
        <p class="login-subtitle">Sign in to your AI Stylist</p>
      </div>

      <!-- Tabs -->
      <div class="login-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          :class="['login-tab', { active: activeTab === tab.value }]"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Login form -->
      <form v-if="activeTab === 'login'" class="login-form" @submit.prevent="submitLogin">
        <label class="field-label">账号</label>
        <input v-model="loginForm.username" class="m-input" placeholder="请输入账号" required />
        <label class="field-label">密码</label>
        <input v-model="loginForm.password" class="m-input" type="password" placeholder="请输入密码" required />
        <button type="submit" class="m-btn-primary submit-btn" :disabled="submitting">
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>

      <!-- Register form -->
      <form v-else class="login-form" @submit.prevent="submitRegister">
        <label class="field-label">账号</label>
        <input v-model="registerForm.username" class="m-input" placeholder="请输入账号" required />
        <label class="field-label">密码</label>
        <input v-model="registerForm.password" class="m-input" type="password" placeholder="请输入密码" required />
        <label class="field-label">确认密码</label>
        <input v-model="registerForm.confirm" class="m-input" type="password" placeholder="请再次输入密码" required />
        <button type="submit" class="m-btn-primary submit-btn" :disabled="submitting">
          {{ submitting ? '注册中…' : '注册' }}
        </button>
      </form>

      <div class="divider">
        <span>或者</span>
      </div>

      <button class="guest-btn" @click="enterGuest">
        <span class="guest-icon">✦</span>
        <span>游客试玩（已有示例衣橱）</span>
      </button>
      <p class="guest-tip">无需注册，直接体验 AI 推荐 / 虚拟试穿 / 智能对话</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const tabs = [{ value: 'login', label: '登录' }, { value: 'register', label: '注册' }];
const activeTab = ref('login');
const submitting = ref(false);

const loginForm = ref({ username: '', password: '' });
const registerForm = ref({ username: '', password: '', confirm: '' });

const submitLogin = async () => {
  submitting.value = true;
  try {
    const res = await fetch('/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm.value)
    });
    const payload = await res.json();
    if (res.ok && payload.code === 1 && payload.data?.token) {
      localStorage.setItem('auth_token', payload.data.token);
      localStorage.removeItem('guest_mode');
      // 清掉游客身份下缓存的衣橱/试穿/搭配，进入登录用户的干净状态
      app?.setAllClosetItems?.([]);
      app?.setSelectedItems?.([]);
      app?.clearOutfit?.();
      ElMessage.success('登录成功');
      emit('navigate', { page: 'assistant' });
    } else {
      ElMessage.error(payload.msg || '登录失败');
    }
  } catch {
    ElMessage.error('登录异常');
  } finally {
    submitting.value = false;
  }
};

const submitRegister = async () => {
  if (registerForm.value.password !== registerForm.value.confirm) {
    ElMessage.error('两次输入的密码不一致');
    return;
  }
  submitting.value = true;
  try {
    const res = await fetch('/users/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.value.username,
        password: registerForm.value.password
      })
    });
    const payload = await res.json();
    if (res.ok && payload.code === 1) {
      ElMessage.success('注册成功，请登录');
      activeTab.value = 'login';
      loginForm.value.username = registerForm.value.username;
    } else {
      ElMessage.error(payload.msg || '注册失败');
    }
  } catch {
    ElMessage.error('注册异常');
  } finally {
    submitting.value = false;
  }
};

const enterGuest = () => {
  localStorage.setItem('guest_mode', '1');
  localStorage.removeItem('auth_token');
  ElMessage.success('已进入游客试玩模式');
  emit('navigate', { page: 'assistant' });
};
</script>

<style scoped>
.login-page {
  padding-top: 12px;
  background: var(--m-bg);
  padding-bottom: 24px;
}

.page-header { margin-bottom: 20px; }

.login-body {
  padding: 8px 4px;
}

.login-titles { text-align: center; margin-bottom: 32px; }
.login-title { font-size: 30px; font-weight: 800; color: var(--m-text); margin: 0 0 8px; letter-spacing: -0.5px; }
.login-subtitle { font-size: 15px; color: var(--m-text-secondary); margin: 0; }

.login-tabs {
  display: flex;
  background: var(--m-border);
  border-radius: var(--m-radius-xl);
  padding: 4px;
  margin-bottom: 24px;
}
.login-tab {
  flex: 1;
  padding: 11px 0;
  border-radius: var(--m-radius-xl);
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--m-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.login-tab.active {
  background: var(--m-primary);
  color: #fff;
  box-shadow: 0 2px 8px rgba(240, 90, 140, 0.25);
}

.login-form { display: flex; flex-direction: column; gap: 8px; }
.field-label { font-size: 14px; font-weight: 600; color: var(--m-text); margin-top: 8px; }
.submit-btn {
  margin-top: 18px;
  width: 100%;
  padding: 15px;
  font-size: 16px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 24px 0;
  color: var(--m-text-secondary);
  font-size: 13px;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--m-border);
}

.guest-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  background: var(--m-card);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-xl);
  font-size: 15px;
  font-weight: 500;
  color: var(--m-text);
  cursor: pointer;
  transition: all 0.2s;
}
.guest-btn:active { background: var(--m-border); transform: scale(0.99); }
.guest-icon { color: var(--m-primary); font-size: 18px; }
.guest-tip {
  text-align: center;
  font-size: 12px;
  color: var(--m-text-secondary);
  margin: 12px 0 0;
}
</style>
