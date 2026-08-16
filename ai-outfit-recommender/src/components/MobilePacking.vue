<template>
  <div class="m-page packing-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">旅行打包助手</h1>
      <div class="header-spacer"></div>
    </header>

    <div class="packing-form-card">
      <label class="field-label">目的地城市</label>
      <input v-model="city" class="m-input" placeholder="如：东京 / 三亚 / 新疆" />

      <div class="form-row">
        <div class="form-col">
          <label class="field-label">行程天数</label>
          <div class="number-stepper">
            <button @click="days = Math.max(1, days - 1)">-</button>
            <span>{{ days }}</span>
            <button @click="days = Math.min(30, days + 1)">+</button>
          </div>
        </div>
        <div class="form-col">
          <label class="field-label">季节偏好</label>
          <select v-model="season" class="m-input season-select">
            <option value="">不限</option>
            <option value="春">春</option>
            <option value="夏">夏</option>
            <option value="秋">秋</option>
            <option value="冬">冬</option>
          </select>
        </div>
      </div>

      <label class="field-label">出行场景</label>
      <input v-model="purpose" class="m-input" placeholder="休闲度假 / 商务出差 / 海边游玩" />
    </div>

    <button class="m-btn-primary generate-btn" @click="generate" :disabled="loading">
      {{ loading ? '生成中…' : '生成胶囊衣橱清单' }}
    </button>

    <div v-if="result" class="result-card">
      <h3 class="result-head">📍 {{ result.city }} · {{ result.days }} 天<span v-if="result.season"> · {{ result.season }}</span></h3>
      <div v-if="result.items.length" class="pack-list">
        <div v-for="(it, i) in result.items" :key="i" class="pack-item">
          <img v-if="it.url" :src="it.url" class="pack-thumb" />
          <div class="pack-info">
            <div class="pack-name">{{ it.name }} <span class="pack-qty">×{{ it.qty || 1 }}</span></div>
            <div class="pack-reason">{{ it.reason }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-pack">暂未生成清单，调整输入后重试</div>
      <div v-if="result.tips?.length" class="pack-tips">
        <div class="tips-label">打包贴士</div>
        <ul>
          <li v-for="(t, i) in result.tips" :key="i">{{ t }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['back']);

const city = ref('');
const days = ref(3);
const season = ref('');
const purpose = ref('');
const loading = ref(false);
const result = ref(null);

const generate = async () => {
  if (!city.value.trim()) {
    ElMessage.warning('请填写目的地城市');
    return;
  }
  loading.value = true;
  result.value = null;
  try {
    const qs = new URLSearchParams({
      city: city.value.trim(),
      days: String(days.value),
      season: season.value || '',
      purpose: purpose.value || '',
    });
    const res = await fetch(`/recommend/packing?${qs.toString()}`, {
      headers: { Authorization: localStorage.getItem('auth_token') || '' }
    });
    const payload = await res.json();
    const data = payload?.data ?? payload;
    result.value = {
      city: data.city || city.value,
      days: data.days || days.value,
      season: data.season || season.value,
      items: data.items || [],
      tips: data.tips || []
    };
  } catch {
    ElMessage.error('生成失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.packing-page { padding-top: 12px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-spacer { width: 36px; }

.packing-form-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}
.field-label { font-size: 13px; font-weight: 500; color: var(--m-text); }

.form-row { display: flex; gap: 14px; }
.form-col { flex: 1; }

.number-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--m-border);
  border-radius: var(--m-radius-md);
  padding: 4px;
}
.number-stepper button {
  width: 36px;
  height: 36px;
  border-radius: var(--m-radius-md);
  border: none;
  background: var(--m-card);
  color: var(--m-primary);
  font-size: 18px;
  cursor: pointer;
}
.number-stepper span {
  font-size: 16px;
  font-weight: 600;
  color: var(--m-text);
}

.season-select {
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%239CA3AF' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
}

.generate-btn { width: 100%; margin-bottom: 20px; }

.result-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 16px;
  margin-bottom: 20px;
}
.result-head { font-size: 15px; font-weight: 600; margin: 0 0 12px; }
.pack-list { display: flex; flex-direction: column; gap: 10px; }
.pack-item { display: flex; gap: 10px; align-items: center; }
.pack-thumb { width: 48px; height: 48px; border-radius: var(--m-radius-md); object-fit: cover; background: #E5E7EB; }
.pack-info { flex: 1; }
.pack-name { font-size: 13px; font-weight: 500; }
.pack-qty { color: var(--m-primary); font-weight: 600; }
.pack-reason { font-size: 12px; color: var(--m-text-secondary); margin-top: 2px; }
.empty-pack { text-align: center; padding: 20px 0; color: var(--m-text-secondary); font-size: 13px; }
.pack-tips { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--m-border); }
.tips-label { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.pack-tips ul { margin: 0; padding-left: 16px; }
.pack-tips li { font-size: 12px; color: var(--m-text-secondary); margin-bottom: 4px; }
</style>
