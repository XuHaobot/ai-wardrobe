<template>
  <div class="history-panel">
    <div class="panel-head">
      <h3>我的搭配</h3>
      <div class="head-right">
        <el-radio-group v-model="sceneFilter" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="daily">日常</el-radio-button>
          <el-radio-button value="travel">旅行</el-radio-button>
        </el-radio-group>
        <button class="close-x" @click="$emit('close')">✕</button>
      </div>
    </div>

    <div class="panel-body">
      <el-skeleton :rows="3" animated v-if="loading" />
      <div v-else-if="records.length === 0" class="empty">
        <div class="empty-icon">👗</div>
        <p>{{ isGuest ? '游客模式展示演示搭配，登录后可保存自己的' : '还没有保存的搭配，去试试 AI 推荐吧' }}</p>
      </div>

      <div v-for="rec in records" :key="rec.id" class="history-card">
        <div class="history-top">
          <span class="rec-title">{{ rec.title }}</span>
          <span class="scene-badge" :class="rec.scene_type">{{ rec.scene_type === 'travel' ? '旅行' : '日常' }}</span>
        </div>
        <div class="rec-meta" v-if="rec.purpose || rec.weather">
          <span v-if="rec.purpose">🎯 {{ rec.purpose }}</span>
          <span v-if="rec.weather">🌤 {{ rec.weather }}</span>
        </div>
        <div class="thumb-row">
          <img v-for="it in rec.items.slice(0, 5)" :key="it.url" :src="it.url" class="thumb" />
        </div>
        <p class="rec-reason" v-if="rec.reason">{{ rec.reason }}</p>
        <div class="history-foot">
          <span class="date">{{ formatDate(rec.created_at) }}</span>
          <el-button
            v-if="!isGuest"
            size="small"
            text
            type="danger"
            @click="remove(rec.id)"
          >删除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['close']);
const loading = ref(false);
const records = ref([]);
const sceneFilter = ref('all');
const isGuest = computed(() => !localStorage.getItem('auth_token') && localStorage.getItem('guest_mode') === '1');

const fetchHistory = async () => {
  loading.value = true;
  try {
    const qs = sceneFilter.value !== 'all' ? `?scene_type=${sceneFilter.value}` : '';
    const res = await fetch(`/outfit/history${qs}`, {
      headers: (() => {
        const h = new Headers();
        const t = localStorage.getItem('auth_token');
        if (t) h.set('Authorization', t);
        if (!t && localStorage.getItem('guest_mode') === '1') h.set('X-Guest', '1');
        return h;
      })(),
    });
    if (res.ok) {
      const payload = await res.json();
      records.value = payload?.data?.items ?? payload?.items ?? [];
    }
  } catch {
    // ignore
  } finally {
    loading.value = false;
  }
};

const remove = async (id) => {
  try {
    const res = await fetch(`/outfit/history/${id}`, {
      method: 'DELETE',
      headers: { Authorization: localStorage.getItem('auth_token') || '' },
    });
    if (res.ok) {
      records.value = records.value.filter(r => r.id !== id);
      ElMessage.success('已删除');
    } else {
      ElMessage.error('删除失败');
    }
  } catch {
    ElMessage.error('删除失败');
  }
};

const formatDate = (s) => {
  if (!s) return '';
  try { return new Date(s).toLocaleString(); } catch { return s; }
};

onMounted(fetchHistory);
watch(sceneFilter, fetchHistory);
</script>

<style scoped>
.history-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.panel-head h3 { margin: 0; font-size: 16px; }
.head-right { display: flex; align-items: center; gap: 10px; }
.close-x {
  border: none; background: transparent; font-size: 16px; cursor: pointer; color: #86868b;
}
.close-x:hover { color: #1d1d1f; }
.panel-body { flex: 1; overflow-y: auto; padding-top: 14px; }
.empty { text-align: center; color: #86868b; padding: 40px 0; }
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.history-card {
  background: #fafafa;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 12px;
}
.history-top { display: flex; justify-content: space-between; align-items: center; }
.rec-title { font-weight: 600; font-size: 14px; }
.scene-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
}
.scene-badge.daily { background: #eef; color: #556ee0; }
.scene-badge.travel { background: #e6f5ee; color: #0f6e56; }
.rec-meta { display: flex; gap: 12px; font-size: 12px; color: #666; margin: 6px 0; flex-wrap: wrap; }
.thumb-row { display: flex; gap: 6px; flex-wrap: wrap; }
.thumb {
  width: 44px; height: 44px; object-fit: cover; border-radius: 8px; background: #fff;
}
.rec-reason { font-size: 12px; color: #555; margin: 8px 0 4px; line-height: 1.5; }
.history-foot { display: flex; justify-content: space-between; align-items: center; }
.date { font-size: 11px; color: #aaa; }
</style>
