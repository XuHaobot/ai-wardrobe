<template>
  <div class="m-page history-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">我的搭配</h1>
      <div class="header-spacer"></div>
    </header>

    <div v-if="isGuest" class="guest-banner">
      <span>✨</span>
      <span>游客模式下显示示例搭配，登录后可查看真实历史</span>
    </div>

    <div class="history-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="['m-chip', { active: activeTab === tab.value }]"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="history-grid">
      <div
        v-for="item in filteredList"
        :key="item.id"
        class="history-card"
        @click="viewDetail(item)"
      >
        <div class="history-img">
          <img v-if="item.coverUrl" :src="item.coverUrl" />
          <span v-else class="history-placeholder">{{ item.title }}</span>
        </div>
        <h3 class="history-title">{{ item.title }}</h3>
        <span :class="['history-tag', tagClass(item.scene_type)]">{{ sceneLabel(item.scene_type) }}</span>
      </div>
    </div>

    <div v-if="!loading && filteredList.length === 0" class="empty-state">
      <p>暂无保存的搭配</p>
      <button class="m-btn-primary" @click="emit('navigate', { page: 'assistant' })">
        去 AI 助手生成
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const isGuest = computed(() => app.isGuest());

const tabs = [
  { value: 'all', label: '全部' },
  { value: 'daily', label: '日常' },
  { value: 'travel', label: '旅行' },
];
const activeTab = ref('all');
const list = ref([]);
const loading = ref(true);

const filteredList = computed(() => {
  if (activeTab.value === 'all') return list.value;
  return list.value.filter(i => i.scene_type === activeTab.value);
});

const sceneLabel = (type) => ({
  daily: '日常', travel: '旅行', date: '约会', commute: '通勤', gym: '健身'
}[type] || type || '日常');

const tagClass = (type) => {
  if (type === 'date') return 'tag-pink';
  if (type === 'commute') return 'tag-blue';
  if (type === 'gym') return 'tag-green';
  if (type === 'travel') return 'tag-orange';
  return 'tag-pink';
};

const fetchHistory = async () => {
  loading.value = true;
  try {
    if (isGuest.value) {
      list.value = mockList();
      return;
    }
    const res = await fetch('/outfit/history', {
      headers: app.authHeaders()
    });
    const payload = await res.json();
    const data = payload?.data ?? payload;
    const arr = Array.isArray(data) ? data : (data?.list ?? data?.items ?? []);
    list.value = arr.map(i => ({
      id: i.id ?? Math.random(),
      title: i.title || '搭配方案',
      coverUrl: i.items?.[0]?.url || i.items?.[0]?.imageUrl || '',
      scene_type: i.scene_type || 'daily',
      purpose: i.purpose || '',
      reason: i.reason || '',
      items: i.items || []
    }));
  } catch {
    list.value = mockList();
  } finally {
    loading.value = false;
  }
};

const mockList = () => [
  { id: 1, title: '温柔约会风', coverUrl: '', scene_type: 'date', purpose: '约会', reason: '浅粉色针织开衫配白色吊带裙，温柔又有氛围感。', items: [] },
  { id: 2, title: '清爽通勤风', coverUrl: '', scene_type: 'commute', purpose: '通勤', reason: '白衬衫加西裤，干练清爽。', items: [] },
  { id: 3, title: '运动健身风', coverUrl: '', scene_type: 'gym', purpose: '健身', reason: '透气运动套装，舒适排汗。', items: [] },
  { id: 4, title: '周末出游风', coverUrl: '', scene_type: 'travel', purpose: '旅行', reason: '休闲牛仔外套配T恤，轻松出片。', items: [] },
];

const viewDetail = (item) => {
  app.setOutfitResult({
    query: item.purpose || item.title,
    title: item.title,
    reason: item.reason,
    items: item.items.map(i => ({ imageUrl: i.url || i.imageUrl || '', name: i.name || '' }))
  });
  emit('navigate', { page: 'outfit-result' });
};

onMounted(fetchHistory);
</script>

<style scoped>
.history-page { padding-top: 12px; }

.guest-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--m-primary-light);
  color: var(--m-primary);
  padding: 10px 14px;
  border-radius: var(--m-radius-md);
  font-size: 13px;
  margin-bottom: 14px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-spacer { width: 36px; }

.history-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding-bottom: 20px;
}
.history-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.history-card:active { transform: scale(0.98); }
.history-img {
  aspect-ratio: 1;
  background: #E5E7EB;
  border-radius: var(--m-radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}
.history-img img { width: 100%; height: 100%; object-fit: cover; }
.history-placeholder { font-size: 14px; color: #9CA3AF; text-align: center; padding: 0 10px; }
.history-title { font-size: 14px; font-weight: 600; margin: 0 0 8px; }
.history-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
}
.tag-pink { background: #FCE7F3; color: #F05A8C; }
.tag-blue { background: #DBEAFE; color: #2563EB; }
.tag-green { background: #D1FAE5; color: #059669; }
.tag-orange { background: #FFEDD5; color: #EA580C; }

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--m-text-secondary);
}
.empty-state p { margin-bottom: 16px; }
</style>
