<template>
  <div class="m-page tryon-page">
    <header class="tryon-header">
      <h1 class="tryon-title">Virtual Try-On</h1>
      <button class="m-btn-primary tryon-action" @click="doTryOn" :disabled="selectedItems.length === 0 || loading">
        <span>✨</span>
        <span>试穿 ({{ selectedItems.length }}件)</span>
      </button>
    </header>

    <!-- Gender switch -->
    <div class="gender-switch">
      <button :class="['gender-btn', { active: role === 'male' }]" @click="setRole('male')">
        <span>♂</span> Male
      </button>
      <button :class="['gender-btn', { active: role === 'female' }]" @click="setRole('female')">
        <span>♀</span> Female
      </button>
    </div>

    <!-- Selected tags -->
    <div v-if="selectedItems.length > 0" class="selected-tags">
      <span class="tags-label">已选：</span>
      <span
        v-for="(item, idx) in selectedItems"
        :key="idx"
        class="sel-tag"
      >
        {{ item.name }}
        <button class="remove-tag" @click="removeItem(idx)">×</button>
      </span>
    </div>

    <!-- Stage -->
    <div class="stage-card">
      <div v-if="loading" class="stage-state">
        <div class="spinner"></div>
        <p>AI 正在为你生成试穿效果…</p>
        <p class="stage-hint">生图约需 20~90 秒，请稍候</p>
      </div>
      <img v-else-if="resultImage" :src="resultImage" class="result-image" alt="试穿结果" />
      <img v-else :src="baseRoleImage" class="result-image model-base" alt="模特底图" />
    </div>

    <!-- Footer actions：按登录态展示 -->
    <div class="tryon-footer">
      <template v-if="isGuest">
        <button class="guest-link" @click="emit('navigate', { page: 'login' })">
          游客试玩中 · 登录后可保存搭配
        </button>
        <button class="m-btn-primary login-btn" @click="emit('navigate', { page: 'login' })">
          登录 / 注册
        </button>
      </template>
      <template v-else>
        <span class="tryon-tip">在衣橱勾选衣物即可试穿多件</span>
        <button class="m-btn-primary login-btn" @click="emit('navigate', { page: 'wardrobe' })">
          去衣橱选衣物
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate']);
const app = inject('mobileApp');

const role = computed({
  get: () => app.currentRole.value,
  set: (v) => app.setRole(v)
});
const selectedItems = computed(() => app.selectedItems.value);
const isGuest = computed(() => app.isGuest());

const loading = ref(false);
const resultImage = ref('');

const baseRoleImage = computed(() => role.value === 'male' ? '/uploads/男.png' : '/uploads/女.png');

const setRole = (r) => {
  role.value = r;
  resultImage.value = '';
};

const removeItem = (idx) => {
  const list = [...selectedItems.value];
  list.splice(idx, 1);
  app.setSelectedItems(list);
};

const doTryOn = async () => {
  if (selectedItems.value.length === 0) return;
  loading.value = true;
  resultImage.value = '';
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);
    const res = await fetch('/tryon', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...app.authHeaders()
      },
      body: JSON.stringify({
        gender: role.value,
        clothingUrls: selectedItems.value.map(i => i.imageUrl).filter(Boolean)
      }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const payload = await res.json();
    if (payload.code === 1 && payload.data?.success && payload.data.imageUrl) {
      resultImage.value = payload.data.imageUrl;
      ElMessage.success('虚拟试穿成功');
    } else {
      ElMessage.warning(payload.data?.message || 'AI生图暂时不可用，展示基础效果');
      resultImage.value = baseRoleImage.value;
    }
  } catch (e) {
    console.error(e);
    if (e.name === 'AbortError') {
      ElMessage.warning('试穿请求超时');
    } else {
      ElMessage.error('试穿失败');
    }
    resultImage.value = baseRoleImage.value;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.tryon-page { padding-top: 12px; }

.tryon-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.tryon-title { font-size: 22px; font-weight: 700; color: var(--m-text); margin: 0; }
.tryon-action { padding: 8px 14px; font-size: 13px; }

.gender-switch {
  display: flex;
  background: var(--m-card);
  border-radius: var(--m-radius-xl);
  padding: 4px;
  margin-bottom: 16px;
  border: 1px solid var(--m-border);
}
.gender-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  border-radius: var(--m-radius-xl);
  border: none;
  background: transparent;
  color: var(--m-text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.gender-btn.active {
  background: var(--m-primary);
  color: #fff;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.tags-label { font-size: 13px; color: var(--m-primary); }
.sel-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--m-primary-light);
  color: var(--m-primary);
  font-size: 12px;
}
.remove-tag {
  background: transparent;
  border: none;
  color: var(--m-primary);
  font-size: 14px;
  cursor: pointer;
  line-height: 1;
}

.stage-card {
  background: #E5E7EB;
  border-radius: var(--m-radius-xl);
  aspect-ratio: 3 / 4;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 20px;
}
.stage-state {
  text-align: center;
  color: var(--m-text-secondary);
  padding: 20px;
}
.placeholder-text {
  font-size: 28px;
  color: #9CA3AF;
  margin: 0 0 8px;
}
.stage-tip { font-size: 12px; margin: 0; }
.result-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.model-base {
  background: #fff;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(240, 90, 140, 0.2);
  border-top-color: var(--m-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.tryon-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.tryon-tip {
  font-size: 12px;
  color: var(--m-text-secondary);
}
.guest-link {
  background: transparent;
  border: none;
  color: #6366F1;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  text-align: left;
}
.login-btn { padding: 12px 24px; white-space: nowrap; }
.stage-hint { font-size: 12px; opacity: 0.8; margin: 4px 0 0; }
</style>
