<template>
  <div class="m-page upload-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">添加衣物</h1>
      <div class="header-spacer"></div>
    </header>

    <div class="upload-card" @click="fileInput?.click()">
      <div class="upload-icon">📷</div>
      <p class="upload-title">拍照或从相册选择</p>
      <p class="upload-tip">支持 JPG / PNG AI 自动识别分类与颜色</p>
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png"
        capture="environment"
        style="display: none"
        @change="handleFile"
      />
    </div>

    <div class="upload-actions">
      <button class="m-btn-dark" @click="fileInput?.click()">
        <span>📷</span>
        <span>拍照</span>
      </button>
      <button class="m-btn-ghost" @click="fileInput?.click()">
        <span>🖼</span>
        <span>相册</span>
      </button>
    </div>

    <p class="upload-hint" v-if="isGuest">游客模式下无法上传，登录后可添加自己的衣物</p>
    <p class="upload-hint" v-else>登录后可自动同步到衣橱</p>

    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar"><div class="progress-fill" :style="{ width: progress + '%' }"></div></div>
      <p>AI 识别中…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, computed } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const fileInput = ref(null);
const uploading = ref(false);
const progress = ref(30);

const isGuest = computed(() => app.isGuest());

const handleFile = async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  if (isGuest.value) {
    ElMessage.warning('游客模式下无法上传衣物，请先登录');
    return;
  }
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    ElMessage.error('请上传 JPG 或 PNG 图片');
    return;
  }

  uploading.value = true;
  progress.value = 30;

  try {
    const formData = new FormData();
    formData.append('image', file);

    const res = await fetch('/items', {
      method: 'POST',
      headers: app.authHeaders(),
      body: formData
    });

    if (!res.ok) throw new Error('上传失败');

    const payload = await res.json();
    const data = payload?.data ?? payload;
    const newItem = {
      id: data?.id ?? Math.random(),
      name: data?.name ?? file.name,
      imageUrl: data?.url ?? data?.imageUrl ?? '',
      category: data?.category ?? 'all',
      color: data?.color ?? '',
      style: data?.style ?? '',
      description: data?.description ?? ''
    };

    progress.value = 100;
    ElMessage.success('衣物添加成功');
    app.setCurrentItem(newItem);
    emit('navigate', { page: 'item-detail' });
  } catch (e) {
    console.error(e);
    ElMessage.error('上传失败，请重试');
  } finally {
    uploading.value = false;
    progress.value = 30;
    if (fileInput.value) fileInput.value.value = '';
  }
};
</script>

<style scoped>
.upload-page { padding-top: 12px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-spacer { width: 36px; }

.upload-card {
  background: var(--m-card);
  border: 2px dashed var(--m-text-tertiary);
  border-radius: var(--m-radius-xl);
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.2s;
}
.upload-card:active { border-color: var(--m-primary); background: var(--m-primary-light); }
.upload-icon { font-size: 48px; }
.upload-title { font-size: 16px; font-weight: 500; color: var(--m-text); margin: 0; }
.upload-tip { font-size: 12px; color: var(--m-text-secondary); margin: 0; text-align: center; padding: 0 20px; }

.upload-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.upload-actions button { flex: 1; }

.upload-hint {
  text-align: center;
  font-size: 12px;
  color: var(--m-text-secondary);
  margin: 0;
}

.upload-progress {
  margin-top: 24px;
}
.progress-bar {
  height: 6px;
  background: var(--m-border);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
}
.progress-fill {
  height: 100%;
  background: var(--m-primary);
  border-radius: 999px;
  transition: width 0.3s;
}
.upload-progress p { text-align: center; font-size: 13px; color: var(--m-text-secondary); margin: 0; }
</style>
