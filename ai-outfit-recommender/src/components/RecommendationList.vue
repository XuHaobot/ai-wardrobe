<template>
  <div class="rec-container-compact">
    <div v-if="recommendations.length > 0" class="recommendation-list">
      <div
        v-for="(item, index) in recommendations.slice(0, 3)"
        :key="index"
        class="rec-card"
      >
        <div class="rec-card-header">
          <div class="mini-outfit-preview">
            <div
              v-for="(clothing, idx) in item.outfit.slice(0, 3)"
              :key="clothing.id"
              class="mini-clothing-thumb"
              :style="{ zIndex: item.outfit.length - idx, left: idx * 16 + 'px' }"
            >
              <img :src="clothing.imageUrl" class="thumb-img" />
            </div>
          </div>

          <div class="header-info">
            <div class="rec-title">{{ item.title }}</div>
            <div class="rec-meta">
              <el-icon><Sunny /></el-icon> {{ item.weather }}
              <span class="item-count">{{ item.outfit.length }}件</span>
            </div>
          </div>

          <div class="header-actions">
            <el-button
              type="primary"
              size="small"
              round
              class="apply-btn"
              @click="applyOutfit(item.outfit)"
            >
              试穿
            </el-button>
            <div class="detail-btn" @click="openDetail(index)" title="查看详情">
              <el-icon><InfoFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-compact">
      <span class="empty-text">AI Ready to help</span>
    </div>

    <!-- 推荐详情弹窗 -->
    <el-dialog v-model="showDetail" title="推荐详情" width="460px" :append-to-body="true" class="rec-detail-dialog">
      <template v-if="detailIndex >= 0 && recommendations[detailIndex]">
        <div class="detail-meta">
          <span class="detail-title">{{ recommendations[detailIndex].title }}</span>
          <span class="detail-weather">
            <el-icon><Sunny /></el-icon> {{ recommendations[detailIndex].weather }}
          </span>
        </div>
        <div v-if="recommendations[detailIndex].reason" class="detail-reason">
          <div class="reason-label">推荐理由</div>
          <p>{{ recommendations[detailIndex].reason }}</p>
        </div>
        <div class="detail-outfit-section">
          <div class="reason-label">包含衣物</div>
          <div class="detail-outfit-grid">
            <div
              v-for="clothing in recommendations[detailIndex].outfit"
              :key="clothing.id"
              class="detail-outfit-item"
            >
              <img :src="clothing.imageUrl" class="detail-outfit-img" />
              <span class="detail-outfit-name">{{ clothing.name || '衣物' }}</span>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button
          type="primary"
          @click="applyFromDetail"
          class="dialog-apply-btn"
        >
          试穿这套搭配
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Sunny, InfoFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  trigger: {
    type: Number,
    default: 0,
  },
  purpose: {
    type: String,
    default: '',
  },
  city: {
    type: String,
    default: ''
  }
});

const recommendations = ref([]);
const showDetail = ref(false);
const detailIndex = ref(-1);
const emit = defineEmits(['apply-outfit']);

const openDetail = (index) => {
  detailIndex.value = index;
  showDetail.value = true;
};

const applyOutfit = (outfit) => {
  ElMessage.success('已选择搭配，点击试穿按钮生成效果');
  emit('apply-outfit', outfit);
};

const applyFromDetail = () => {
  if (detailIndex.value >= 0 && recommendations.value[detailIndex.value]) {
    applyOutfit(recommendations.value[detailIndex.value].outfit);
    showDetail.value = false;
  }
};

const normalizeOutfit = (arr) => {
  const urls = Array.isArray(arr) ? arr : [arr].filter(Boolean);
  return urls
    .filter(Boolean)
    .map(u => {
      if (typeof u === 'string') {
        return { id: u, imageUrl: u };
      }
      return {
        id: u.id ?? u.url ?? u.imageUrl ?? Math.random(),
        imageUrl: u.url ?? u.imageUrl ?? ''
      };
    })
    .filter(x => x.imageUrl);
};

const parseRecommendationPayload = (payload) => {
  const data = payload?.data ?? payload?.result ?? payload;

  // 列表格式（新的多推荐响应）
  const listLike = Array.isArray(data)
    ? data
    : (data?.list ?? data?.items ?? data?.records ?? data?.rows);

  if (Array.isArray(listLike) && listLike.length > 0) {
    // 检查第一个元素是否有outfit/urls字段（区分推荐列表和纯URL列表）
    const first = listLike[0];
    if (first && (first.outfit || first.urls || first.images || first.title || first.reason)) {
      return listLike
        .map(r => ({
          title: r.title ?? 'AI 推荐套装',
          weather: r.weather ?? '自动',
          reason: r.description ?? r.desc ?? r.reason ?? '',
          outfit: normalizeOutfit(r.outfit ?? r.urls ?? r.images ?? [r.url ?? r.imageUrl].filter(Boolean))
        }))
        .filter(x => x.outfit.length);
    }
    // 纯URL字符串列表（向后兼容）
    return [{
      title: 'AI 推荐套装',
      weather: '自动',
      reason: '',
      outfit: normalizeOutfit(listLike)
    }].filter(x => x.outfit.length);
  }

  // 单个对象格式（向后兼容）
  const desc = data?.description ?? data?.desc ?? data?.reason ?? '';
  const urlsArr = data?.urls ?? data?.images ?? (data?.outfit ?? []);
  const singleUrl = data?.url ?? data?.imageUrl;
  const outfit = normalizeOutfit(urlsArr?.length ? urlsArr : (singleUrl ? [singleUrl] : []));
  return outfit.length ? [{
    title: data?.title ?? 'AI 推荐套装',
    weather: data?.weather ?? '自动',
    reason: desc,
    outfit
  }] : [];
};

const fetchRecommendations = async () => {
  try {
    const qs = new URLSearchParams();
    if (props.purpose) qs.set('purpose', props.purpose);
    if (props.city && props.city.trim()) qs.set('city', props.city.trim());
    const url = qs.toString() ? `/recommend?${qs.toString()}` : '/recommend';

    // AI 推荐生成耗时较长，设置 60 秒超时（覆盖全局 10 秒）
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 60000);

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': localStorage.getItem('auth_token') || ''
      },
      signal: controller.signal
    });
    clearTimeout(timer);

    if (!res.ok) throw new Error('Network Error');
    const payload = await res.json();
    const mapped = parseRecommendationPayload(payload);
    recommendations.value = mapped;
    if (!mapped.length) {
      ElMessage.info('暂无推荐结果');
    }
  } catch (e) {
    console.error('Fetch error:', e);
    if (e.name === 'AbortError') {
      ElMessage.warning('推荐请求超时，请稍后重试');
    } else {
      ElMessage.error('获取推荐失败');
    }
    recommendations.value = [];
  }
};

watch(() => props.trigger, (val) => {
  if (val) fetchRecommendations();
});
</script>

<style scoped>
.rec-container-compact {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rec-card {
  background: white;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.rec-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.rec-card-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  gap: 10px;
}

.mini-outfit-preview {
  position: relative;
  width: 52px;
  height: 40px;
  flex-shrink: 0;
}
.mini-clothing-thumb {
  position: absolute;
  top: 0;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  background: #f5f5f7;
  border: 1px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}
.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.header-info {
  flex: 1;
  min-width: 0;
}
.rec-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rec-meta {
  font-size: 11px;
  color: #86868b;
  display: flex;
  align-items: center;
  gap: 4px;
}
.item-count {
  margin-left: 4px;
  background: rgba(0,0,0,0.04);
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.apply-btn {
  font-size: 11px;
  padding: 4px 12px;
  height: auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.detail-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0,0,0,0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #86868b;
  transition: all 0.2s;
  font-size: 14px;
}
.detail-btn:hover {
  background: rgba(102, 126, 234, 0.12);
  color: #667eea;
}

.empty-compact {
  text-align: center;
  padding: 10px;
  color: #86868b;
  font-size: 13px;
  opacity: 0.6;
}

/* 弹窗内容 */
.detail-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.detail-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
}
.detail-weather {
  font-size: 12px;
  color: #86868b;
  display: flex;
  align-items: center;
  gap: 3px;
}

.detail-reason {
  background: rgba(102, 126, 234, 0.04);
  border-radius: 10px;
  border-left: 3px solid #667eea;
  padding: 10px 14px;
  margin-bottom: 16px;
}
.detail-reason p {
  margin: 0;
  font-size: 13px;
  color: #555;
  line-height: 1.7;
}
.reason-label {
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
  margin-bottom: 8px;
}

.detail-outfit-section {
  margin-top: 4px;
}
.detail-outfit-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.detail-outfit-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.detail-outfit-img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: contain;
  border-radius: 8px;
  background: #f5f5f7;
  border: 1px solid rgba(0,0,0,0.04);
}
.detail-outfit-name {
  font-size: 10px;
  color: #888;
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialog-apply-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}
</style>
