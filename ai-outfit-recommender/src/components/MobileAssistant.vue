<template>
  <div class="m-page assistant-page">
    <!-- Header -->
    <header class="assistant-header">
      <div class="greeting">早上好 Alex</div>
      <h1 class="date-title">{{ today }}</h1>
    </header>

    <!-- Weather card -->
    <div class="weather-card">
      <div class="weather-main">
        <div class="weather-icon">☀️</div>
        <div class="weather-temp">28°C</div>
      </div>
      <div class="weather-meta">
        <div class="weather-city">📍 广州</div>
        <div class="weather-desc">适合穿轻薄外套</div>
      </div>
      <div class="weather-status">晴朗</div>
    </div>

    <!-- Scene shortcuts -->
    <section class="scene-section">
      <h3 class="section-title">今天要去哪？</h3>
      <div class="scene-grid">
        <button
          v-for="scene in scenes"
          :key="scene.value"
          class="scene-card"
          @click="askScene(scene.value, scene.label)"
        >
          <span class="scene-emoji">{{ scene.icon }}</span>
          <span class="scene-label">{{ scene.label }}</span>
        </button>
      </div>
    </section>

    <!-- AI Input -->
    <section class="ai-section">
      <div class="ai-title">
        <span class="ai-icon">✦</span>
        <span>AI 搭配助手</span>
      </div>
      <div class="ai-input-wrap">
        <input
          v-model="query"
          class="m-input ai-input"
          placeholder="今天要去哪里？（如：约会、健身）"
          @keyup.enter="submitQuery"
        />
        <button class="ai-send" @click="submitQuery" :disabled="!query.trim() || loading">
          <span>✦</span>
        </button>
      </div>
      <div class="suggestion-chips">
        <span class="suggestion-label">试试这样问</span>
        <button
          v-for="s in suggestions"
          :key="s"
          class="suggestion-chip"
          @click="query = s; submitQuery()"
        >
          {{ s }}
        </button>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>AI 正在为你搭配…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue';
import { ElMessage } from 'element-plus';

const app = inject('mobileApp');

const emit = defineEmits(['navigate']);

const query = ref('');
const loading = ref(false);

const today = computed(() => {
  const d = new Date();
  return `${d.getMonth() + 1}月${d.getDate()}日 ${['周日','周一','周二','周三','周四','周五','周六'][d.getDay()]}`;
});

const scenes = [
  { value: 'date', label: '约会', icon: '💕' },
  { value: 'gym', label: '健身', icon: '🏃' },
  { value: 'commute', label: '通勤', icon: '💼' },
];

const suggestions = ['帮我搭一套面试装', '周末出游怎么穿'];

const askScene = (value, label) => {
  query.value = `我要${label}，怎么穿？`;
  submitQuery();
};

const submitQuery = async () => {
  if (!query.value.trim()) return;
  loading.value = true;

  const purpose = query.value.trim();

  try {
    const res = await fetch(`/recommend?purpose=${encodeURIComponent(purpose)}`, {
      headers: app.authHeaders()
    });
    const payload = await res.json();

    // 解析推荐结果（简化版）
    const data = payload?.data ?? payload?.result ?? payload;
    let list = [];
    if (Array.isArray(data)) list = data;
    else if (Array.isArray(data?.list)) list = data.list;
    else if (data) list = [data];

    const rec = list[0];
    const outfitResult = {
      query: purpose,
      title: rec?.title ?? 'AI 搭配方案',
      reason: rec?.description ?? rec?.reason ?? `${purpose}穿搭建议已生成，请点击试穿查看效果`,
      items: (rec?.outfit ?? rec?.urls ?? rec?.images ?? []).map(u => typeof u === 'string' ? { imageUrl: u, name: '' } : u),
    };

    app.setOutfitResult(outfitResult);
    emit('navigate', { page: 'outfit-result' });
  } catch (e) {
    console.error(e);
    ElMessage.error('搭配推荐失败');
  } finally {
    loading.value = false;
    query.value = '';
  }
};
</script>

<style scoped>
.assistant-page { padding-top: 12px; }

.assistant-header { margin-bottom: 16px; }
.greeting { font-size: 15px; color: var(--m-text-secondary); margin-bottom: 4px; }
.date-title { font-size: 26px; font-weight: 700; color: var(--m-text); margin: 0; }

.weather-card {
  background: linear-gradient(135deg, var(--m-accent-orange) 0%, var(--m-primary) 100%);
  border-radius: var(--m-radius-xl);
  padding: 18px 20px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  box-shadow: var(--m-shadow);
}
.weather-main { display: flex; align-items: center; gap: 10px; }
.weather-icon { font-size: 32px; }
.weather-temp { font-size: 36px; font-weight: 700; }
.weather-meta { text-align: right; }
.weather-city { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.weather-desc { font-size: 12px; opacity: 0.9; }
.weather-status { display: none; }

.section-title { font-size: 16px; font-weight: 600; color: var(--m-text); margin: 0 0 12px; }

.scene-grid { display: flex; gap: 12px; margin-bottom: 24px; }
.scene-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  background: var(--m-card);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}
.scene-card:active { transform: scale(0.98); }
.scene-emoji { font-size: 28px; }
.scene-label { font-size: 13px; font-weight: 500; color: var(--m-text); }

.ai-section { background: var(--m-card); border-radius: var(--m-radius-lg); padding: 16px; }
.ai-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--m-text); margin-bottom: 12px; }
.ai-icon { color: var(--m-primary); }
.ai-input-wrap { position: relative; margin-bottom: 14px; }
.ai-input { padding-right: 50px; }
.ai-send {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--m-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.ai-send:disabled { opacity: 0.5; }

.suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.suggestion-label { font-size: 12px; color: var(--m-text-secondary); margin-right: 4px; }
.suggestion-chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--m-primary-light);
  background: var(--m-primary-light);
  color: var(--m-primary);
  font-size: 12px;
  cursor: pointer;
}

.loading-state {
  text-align: center;
  padding: 40px 0;
  color: var(--m-text-secondary);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(240, 90, 140, 0.2);
  border-top-color: var(--m-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
