<template>
  <div class="m-page result-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">AI 搭配方案</h1>
      <div class="header-spacer"></div>
    </header>

    <div v-if="result" class="result-content">
      <div class="user-bubble">
        {{ result.query }}
      </div>

      <h2 class="result-title">{{ result.title }}</h2>

      <div class="result-image-card">
        <img v-if="result.items.length && result.items[0].imageUrl" :src="result.items[0].imageUrl" />
        <p v-else class="placeholder-text">搭配效果图</p>
      </div>

      <div class="items-section">
        <h3 class="section-label">搭配单品</h3>
        <div class="items-row">
          <div
            v-for="(item, idx) in result.items.slice(0, 8)"
            :key="idx"
            class="item-chip"
          >
            {{ item.name || '单品' + (idx + 1) }}
          </div>
        </div>
      </div>

      <div class="reason-card">
        {{ result.reason }}
      </div>

      <div class="action-bar">
        <button class="m-btn-primary try-btn" @click="tryThis">
          <span>🪞</span>
          <span>试穿这套</span>
        </button>
        <button class="m-btn-ghost save-btn" @click="saveOutfit">
          <span>♥</span>
          <span>保存搭配</span>
        </button>
      </div>
    </div>

    <div v-else class="empty-result">
      <p>暂无搭配结果</p>
      <button class="m-btn-primary" @click="emit('navigate', { page: 'assistant', replace: true })">
        返回重新提问
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const result = computed(() => app.currentOutfitResult.value);

const tryThis = () => {
  if (!result.value?.items?.length) return;
  app.setSelectedItems(result.value.items.map(i => ({
    id: i.id ?? Math.random(),
    name: i.name || '',
    imageUrl: i.imageUrl || i.url || ''
  })).filter(i => i.imageUrl));
  emit('navigate', { page: 'tryon' });
};

const saveOutfit = async () => {
  if (!result.value?.items?.length) return;
  if (!localStorage.getItem('auth_token')) {
    ElMessage.warning('登录后即可保存搭配到「我的搭配」');
    return;
  }
  try {
    const items = result.value.items.map(c => ({ url: c.imageUrl || c.url || '', name: c.name || '' }));
    const res = await fetch('/outfit/history', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: localStorage.getItem('auth_token') || ''
      },
      body: JSON.stringify({
        title: result.value.title,
        items,
        reason: result.value.reason,
        purpose: result.value.query,
        scene_type: 'daily',
      })
    });
    const payload = await res.json();
    if (res.ok && payload.code === 1) {
      ElMessage.success('已保存到「我的搭配」');
    } else {
      ElMessage.error(payload.msg || '保存失败');
    }
  } catch {
    ElMessage.error('保存失败');
  }
};
</script>

<style scoped>
.result-page { padding-top: 12px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-spacer { width: 36px; }

.result-content { animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.user-bubble {
  background: var(--m-dark);
  color: #fff;
  padding: 14px 16px;
  border-radius: var(--m-radius-lg);
  border-bottom-left-radius: 6px;
  font-size: 14px;
  margin-bottom: 16px;
}

.result-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--m-text);
  margin: 0 0 14px;
}

.result-image-card {
  background: #E5E7EB;
  border-radius: var(--m-radius-xl);
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 16px;
}
.result-image-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.placeholder-text {
  font-size: 24px;
  color: #9CA3AF;
}

.items-section { margin-bottom: 16px; }
.section-label { font-size: 13px; color: var(--m-text-secondary); margin: 0 0 10px; }
.items-row { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; }
.items-row::-webkit-scrollbar { display: none; }
.item-chip {
  flex-shrink: 0;
  padding: 10px 16px;
  background: var(--m-card);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-md);
  font-size: 13px;
  color: var(--m-text);
}

.reason-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 14px 16px;
  font-size: 14px;
  color: var(--m-text);
  line-height: 1.7;
  margin-bottom: 20px;
}

.action-bar {
  display: flex;
  gap: 12px;
  position: fixed;
  bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  left: 16px;
  right: 16px;
}
.action-bar button { flex: 1; }
.try-btn { font-size: 15px; }
.save-btn { font-size: 15px; }

.empty-result {
  text-align: center;
  padding-top: 60px;
  color: var(--m-text-secondary);
}
</style>
