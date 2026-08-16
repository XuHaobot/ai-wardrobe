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

      <div class="reason-card">
        {{ result.reason }}
      </div>

      <!-- AI 推荐单品：用户自行选择添加 -->
      <div class="items-section">
        <h3 class="section-label">AI 推荐单品 · 点「添加」选入你的搭配</h3>
        <div class="items-grid">
          <div
            v-for="item in suggestionItems"
            :key="item.id"
            :class="['sug-card', { added: isAdded(item) }]"
          >
            <div class="sug-img">
              <img v-if="item.imageUrl" :src="item.imageUrl" alt="" />
              <span v-else class="sug-ph">单品</span>
            </div>
            <p class="sug-name">{{ item.name || '单品' }}</p>
            <button
              v-if="!isAdded(item)"
              class="sug-add"
              @click="addItem(item)"
            >＋ 添加</button>
            <button
              v-else
              class="sug-added"
              @click="removeItem(item)"
            >✓ 已添加</button>
          </div>
        </div>
      </div>

      <!-- 用户自行搭建的「我的搭配」：不预留，添加后才出现 -->
      <div v-if="myItems.length > 0" class="myoutfit-card">
        <div class="myoutfit-head">
          <h3 class="section-label">我的搭配（{{ myItems.length }} 件）</h3>
          <button class="myoutfit-clear" @click="app.clearOutfit()">清空</button>
        </div>
        <div class="myoutfit-row">
          <div v-for="item in myItems" :key="item.id" class="myoutfit-chip">
            <span class="chip-name">{{ item.name || '单品' }}</span>
            <button class="chip-del" @click="removeItem(item)">×</button>
          </div>
        </div>

        <div class="action-bar">
          <button class="m-btn-primary try-btn" @click="goTryOn">
            <span>🎨</span>
            <span>试穿这套</span>
          </button>
          <button class="m-btn-ghost save-btn" @click="saveOutfit">
            <span>♥</span>
            <span>保存搭配</span>
          </button>
        </div>
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
const myItems = computed(() => app.myOutfit.value);
const isGuest = computed(() => app.isGuest());

const suggestionItems = computed(() =>
  (result.value?.items ?? []).map((i, idx) => ({
    id: i.id ?? `sug_${idx}`,
    name: i.name || '',
    imageUrl: i.imageUrl || i.url || '',
  }))
);

const isAdded = (item) => myItems.value.some(i => i.id === item.id);

const addItem = (item) => {
  app.addToOutfit({ id: item.id, name: item.name, imageUrl: item.imageUrl });
  ElMessage.success('已加入我的搭配');
};
const removeItem = (item) => app.removeFromOutfit(item);

const goTryOn = () => {
  if (myItems.value.length === 0) return;
  app.setSelectedItems([...myItems.value]);
  emit('navigate', { page: 'tryon' });
};

const saveOutfit = async () => {
  if (myItems.value.length === 0) return;
  if (isGuest.value) {
    ElMessage.warning('游客模式下无法保存搭配，请先登录');
    return;
  }
  try {
    const items = myItems.value.map(c => ({ url: c.imageUrl || '', name: c.name || '' }));
    const res = await fetch('/outfit/history', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...app.authHeaders()
      },
      body: JSON.stringify({
        title: result.value?.title || '我的搭配',
        items,
        reason: result.value?.reason || '',
        purpose: result.value?.query || '',
        scene_type: 'daily',
      })
    });
    const payload = await res.json();
    if (res.ok && payload.code === 1) {
      ElMessage.success('已保存到「我的搭配」');
      app.clearOutfit();
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

.reason-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 14px 16px;
  font-size: 14px;
  color: var(--m-text);
  line-height: 1.7;
  margin-bottom: 20px;
}

.section-label { font-size: 13px; color: var(--m-text-secondary); margin: 0 0 12px; }

.items-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.sug-card {
  background: var(--m-card);
  border: 2px solid transparent;
  border-radius: var(--m-radius-lg);
  padding: 12px;
  transition: all 0.2s;
}
.sug-card.added { border-color: var(--m-primary); }
.sug-img {
  aspect-ratio: 1;
  background: #fff;
  border-radius: var(--m-radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}
.sug-img img { width: 100%; height: 100%; object-fit: contain; }
.sug-ph { font-size: 14px; color: #9CA3AF; }
.sug-name {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--m-text);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sug-add, .sug-added {
  width: 100%;
  padding: 9px 0;
  border-radius: var(--m-radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.sug-add { background: var(--m-primary); color: #fff; }
.sug-added { background: var(--m-primary-light); color: var(--m-primary); }

.myoutfit-card {
  background: var(--m-card);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-lg);
  padding: 14px 16px;
  margin-bottom: 24px;
}
.myoutfit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.myoutfit-head .section-label { margin: 0; }
.myoutfit-clear {
  background: transparent;
  border: none;
  color: var(--m-text-secondary);
  font-size: 12px;
  cursor: pointer;
}
.myoutfit-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.myoutfit-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px 7px 14px;
  background: var(--m-primary-light);
  color: var(--m-primary);
  border-radius: 999px;
  font-size: 12px;
}
.chip-del {
  background: transparent;
  border: none;
  color: var(--m-primary);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
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
