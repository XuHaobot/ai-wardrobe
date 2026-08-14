<template>
  <el-dialog
    v-model="visible"
    title="旅行打包助手"
    width="520px"
    :append-to-body="true"
    @open="reset"
  >
    <div class="packing-form">
      <div class="form-row">
        <label>目的地城市</label>
        <el-input v-model="city" placeholder="如 东京 / 三亚" size="default" />
      </div>
      <div class="form-row two">
        <div>
          <label>行程天数</label>
          <el-input-number v-model="days" :min="1" :max="30" />
        </div>
        <div>
          <label>季节偏好</label>
          <el-select v-model="season" placeholder="不限" clearable>
            <el-option label="春" value="春" />
            <el-option label="夏" value="夏" />
            <el-option label="秋" value="秋" />
            <el-option label="冬" value="冬" />
          </el-select>
        </div>
      </div>
      <div class="form-row">
        <label>出行场景</label>
        <el-input v-model="purpose" placeholder="如 休闲度假 / 商务出差 / 海边游玩" />
      </div>
      <el-button type="primary" :loading="loading" @click="run" class="run-btn">
        生成胶囊衣橱清单
      </el-button>
    </div>

    <div v-if="result" class="packing-result">
      <div class="result-head">
        📍 {{ result.city }} · {{ result.days }} 天<span v-if="result.season"> · {{ result.season }}</span>
      </div>
      <div v-if="result.items.length" class="pack-list">
        <div v-for="(it, i) in result.items" :key="i" class="pack-item">
          <img :src="it.url" class="pack-thumb" />
          <div class="pack-info">
            <div class="pack-name">{{ it.name }} <span class="pack-qty">×{{ it.qty }}</span></div>
            <div class="pack-reason">{{ it.reason }}</div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂未生成清单，调整输入再试" :image-size="60" />
      <div v-if="result.tips.length" class="pack-tips">
        <div class="tips-label">打包贴士</div>
        <li v-for="(t, i) in result.tips" :key="i">{{ t }}</li>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

const visible = ref(false);
const city = ref('');
const days = ref(3);
const season = ref('');
const purpose = ref('');
const loading = ref(false);
const result = ref(null);

const reset = () => {
  result.value = null;
};

const run = async () => {
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
      headers: (() => {
        const h = new Headers();
        const t = localStorage.getItem('auth_token');
        if (t) h.set('Authorization', t);
        if (!t && localStorage.getItem('guest_mode') === '1') h.set('X-Guest', '1');
        return h;
      })(),
    });
    const payload = await res.json();
    const data = payload?.data ?? payload;
    result.value = {
      city: data.city || city.value,
      days: data.days || days.value,
      season: data.season || season.value,
      items: data.items || [],
      tips: data.tips || [],
    };
    if (!result.value.items.length) {
      ElMessage.info('未生成清单，可调整场景或城市后重试');
    }
  } catch {
    ElMessage.error('生成失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

defineExpose({ open: () => { visible.value = true; } });
</script>

<style scoped>
.packing-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; flex-direction: column; gap: 6px; }
.form-row.two { flex-direction: row; gap: 16px; }
.form-row.two > div { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.form-row label { font-size: 13px; color: #555; font-weight: 500; }
.run-btn { width: 100%; margin-top: 4px; }
.packing-result { margin-top: 18px; border-top: 1px solid rgba(0,0,0,0.06); padding-top: 14px; }
.result-head { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
.pack-list { display: flex; flex-direction: column; gap: 10px; }
.pack-item { display: flex; gap: 10px; align-items: center; }
.pack-thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 8px; background: #f5f5f7; }
.pack-info { flex: 1; }
.pack-name { font-size: 13px; font-weight: 500; }
.pack-qty { color: #667eea; font-weight: 600; }
.pack-reason { font-size: 12px; color: #777; line-height: 1.4; }
.pack-tips { margin-top: 14px; background: #fafafa; border-radius: 10px; padding: 10px 14px; }
.tips-label { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.pack-tips li { font-size: 12px; color: #666; margin-bottom: 4px; }
</style>
