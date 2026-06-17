<template>
  <div class="auth-container">
    <div class="auth-card glass-effect">
      <div class="auth-header">
        <h2 class="auth-title">Welcome Back</h2>
        <p class="auth-subtitle">Sign in to your AI Stylist</p>
      </div>

      <el-tabs v-model="activeTab" class="custom-tabs" :stretch="true">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-position="top" size="large">
            <el-form-item label="账号" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入账号" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="submitLogin" class="submit-btn">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-position="top" size="large">
            <el-form-item label="账号" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入账号" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input v-model="registerForm.confirm" type="password" placeholder="请再次输入密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="submitRegister" class="submit-btn" plain>注册账号</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

const router = useRouter();
const activeTab = ref('login');
const submitting = ref(false);

const loginFormRef = ref();
const registerFormRef = ref();

const loginForm = ref({
  username: '',
  password: ''
});
const registerForm = ref({
  username: '',
  password: '',
  confirm: ''
});

const loginRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};
const registerRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => {
        if (value !== registerForm.value.password) callback(new Error('两次输入的密码不一致'));
        else callback();
      }, trigger: 'blur'
    }
  ]
};

const submitLogin = () => {
  if (!loginFormRef.value) return;
  loginFormRef.value.validate(async (valid) => {
    if (!valid) return;
    submitting.value = true;
    try {
      const res = await fetch('/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm.value)
      });
      if (res.ok) {
        const payload = await res.json();
        // 检查业务状态码：code=1 成功，code=0 失败
        if (payload.code === 1 && payload.data) {
          const data = payload.data;
          const token = data.token || '';
          if (token) {
            localStorage.setItem('auth_token', token);
            ElMessage.success('登录成功');
            router.push('/');
          } else {
            ElMessage.error('登录失败：未返回Token');
          }
        } else {
          ElMessage.error(payload.msg || '登录失败：用户名或密码错误');
        }
      } else {
        ElMessage.error('服务器错误：' + res.status);
      }
    } catch {
      ElMessage.error('登录异常');
    } finally {
      submitting.value = false;
    }
  });
};

const submitRegister = () => {
  if (!registerFormRef.value) return;
  registerFormRef.value.validate(async (valid) => {
    if (!valid) return;
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
      if (res.ok) {
        const payload = await res.json();
        // 检查业务状态码：code=1 成功，code=0 失败
        if (payload.code === 1) {
          ElMessage.success('注册成功，请登录');
          activeTab.value = 'login';
        } else {
          ElMessage.error(payload.msg || '注册失败');
        }
      } else {
        ElMessage.error('服务器错误：' + res.status);
      }
    } catch {
      ElMessage.error('注册异常');
    } finally {
      submitting.value = false;
    }
  });
};

const resetLogin = () => {
  loginForm.value.username = '';
  loginForm.value.password = '';
};
const resetRegister = () => {
  registerForm.value.username = '';
  registerForm.value.password = '';
  registerForm.value.confirm = '';
};
</script>

<style scoped>
.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}

.auth-card {
  width: 420px;
  padding: 40px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.65);
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}
.auth-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}
.auth-subtitle {
  color: #666;
  font-size: 14px;
}

.submit-btn {
  width: 100%;
  margin-top: 10px;
  height: 44px;
  font-size: 16px;
}

/* Customize Tabs */
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: transparent;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  color: #666;
}
:deep(.el-tabs__item.is-active) {
  color: var(--accent-color);
  font-weight: 600;
}
</style>
