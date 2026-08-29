<template>
  <div class="m-page assistant-page">
    <!-- Header -->
    <header class="assistant-header">
      <div class="greeting">{{ greeting }}</div>
      <h1 class="date-title">{{ today }}</h1>
    </header>

    <!-- Weather card（真实数据：IP 定位城市 + 高德天气；失败时降级展示） -->
    <div :class="['weather-card', { 'weather-card--flat': weatherFailed }]">
      <!-- 加载中 -->
      <div v-if="weatherLoading" class="weather-main">
        <div class="weather-icon weather-icon--dim">⏳</div>
        <div class="weather-temp weather-temp--dim">--°</div>
        <div class="weather-meta">
          <div class="weather-city">正在获取天气…</div>
        </div>
      </div>
      <!-- 失败降级：不再展示写死的假数据 -->
      <template v-else-if="weatherFailed">
        <div class="weather-main">
          <div class="weather-icon">🌐</div>
          <div class="weather-meta">
            <div class="weather-city">天气服务暂不可用</div>
            <div class="weather-desc">不影响穿搭推荐，点击可重试</div>
          </div>
        </div>
        <button class="weather-retry" @click="loadWeather">重试</button>
      </template>
      <!-- 正常展示 -->
      <template v-else>
        <div class="weather-main">
          <div class="weather-icon">{{ weather.icon }}</div>
          <div class="weather-temp">{{ weather.temp }}°C</div>
        </div>
        <div class="weather-meta">
          <div class="weather-city">📍 {{ weather.city }}</div>
          <div class="weather-desc">{{ weather.advice }}</div>
        </div>
        <div class="weather-status">{{ weather.condition }}</div>
      </template>
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

    <!-- Loading：AI 推荐需 10~40 秒，明确告知避免误以为卡死 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>AI 正在分析你的衣橱并生成搭配…</p>
      <p class="loading-hint">通常需要 10~40 秒，请稍候</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

const app = inject('mobileApp');

const emit = defineEmits(['navigate']);

const query = ref('');
const loading = ref(false);

const today = computed(() => {
  const d = new Date();
  return `${d.getMonth() + 1}月${d.getDate()}日 ${['周日','周一','周二','周三','周四','周五','周六'][d.getDay()]}`;
});

// 按时间段问候（不再写死「早上好 Alex」）
const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '夜深了';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

// ---------- 真实天气 ----------
const weatherLoading = ref(true);
const weatherFailed = ref(false);
const weather = ref({ city: '', temp: '', condition: '', icon: '☀️', advice: '' });
const locatedCity = ref(''); // 定位到的城市，随推荐请求发给后端

const WEATHER_ICON_RULES = [
  [/雷/, '⛈️'], [/雪/, '❄️'], [/雨/, '🌧️'], [/雾|霾/, '🌫️'],
  [/阴/, '☁️'], [/多云/, '⛅'], [/晴/, '☀️'],
];
const ADVICE_RULES = [
  [/雷/, '有雷雨，记得带伞'],
  [/雨/, '有雨，出门带伞'],
  [/雪/, '下雪了，注意保暖'],
  [/雾|霾/, '有雾霾，建议戴口罩'],
  [/晴/, '天气不错，适合出门'],
];
const pickByRules = (rules, fallback, text) => {
  for (const [re, val] of rules) if (re.test(text)) return val;
  return fallback;
};

// 后端 /weather 返回格式化字符串："城市：xx，天气：xx，温度：xx℃，…"
const parseWeatherText = (text) => {
  if (typeof text !== 'string') return null;
  const temp = text.match(/温度：(-?\d+)/)?.[1];
  if (!temp) return null;
  const city = text.match(/城市：(.+?)，/)?.[1] || '';
  const condition = text.match(/天气：(.+?)，/)?.[1] || '';
  return {
    city,
    temp,
    condition,
    icon: pickByRules(WEATHER_ICON_RULES, '🌡️', condition),
    advice: pickByRules(ADVICE_RULES, '根据天气挑一套合适的穿搭吧'),
  };
};

const loadWeather = async () => {
  weatherLoading.value = true;
  weatherFailed.value = false;
  try {
    // 1. IP 定位城市（失败则用默认城市查天气）
    let city = '';
    try {
      const locRes = await fetch('/api/locate/ip');
      const locPayload = await locRes.json();
      if (locPayload?.code === 1 && locPayload.data?.city) city = locPayload.data.city;
    } catch { /* 定位失败不阻塞天气查询 */ }
    if (!city) city = '北京';

    // 2. 查询该城市实时天气
    const res = await fetch(`/weather?city=${encodeURIComponent(city)}`);
    const payload = await res.json();
    const parsed = parseWeatherText(payload?.data);
    if (parsed) {
      weather.value = parsed;
      locatedCity.value = parsed.city;
    } else {
      weatherFailed.value = true;
    }
  } catch {
    weatherFailed.value = true;
  } finally {
    weatherLoading.value = false;
  }
};

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

// 推荐 URL 映射回衣橱真实衣物，补充名称/类别
const enrichItems = (urls = []) => {
  const closet = app.allClosetItems.value || [];
  return urls.map(u => {
    if (typeof u !== 'string') return u;
    const hit = closet.find(c => c.imageUrl === u);
    return {
      imageUrl: u,
      name: hit?.name || '',
      category: hit?.category || '',
    };
  });
};

// 首次进入（未打开过衣橱 Tab）时预取衣橱：让推荐结果带上真实衣物名
const prefetchCloset = async () => {
  if ((app.allClosetItems.value || []).length > 0) return;
  try {
    const res = await fetch('/closet/items?page=1&size=1000', { headers: app.authHeaders() });
    if (!res.ok) return;
    const payload = await res.json();
    const list = payload?.data ?? payload?.result ?? payload;
    const arr = Array.isArray(list) ? list : (list?.items ?? []);
    const mapped = (Array.isArray(arr) ? arr : []).map(d => ({
      id: d.id ?? Math.random(),
      name: d.name ?? '',
      imageUrl: d.url ?? d.imageUrl ?? '',
    })).filter(x => x.imageUrl);
    app.setAllClosetItems(mapped);
  } catch { /* 预取失败不影响主流程 */ }
};

const submitQuery = async () => {
  if (!query.value.trim()) return;
  loading.value = true;

  const purpose = query.value.trim();

  try {
    const cityParam = locatedCity.value ? `&city=${encodeURIComponent(locatedCity.value)}` : '';
    const res = await fetch(`/recommend?purpose=${encodeURIComponent(purpose)}${cityParam}`, {
      headers: app.authHeaders()
    });
    const payload = await res.json();

    if (payload?.code !== 1) {
      ElMessage.error(payload?.message || '搭配推荐失败，请稍后再试');
      return;
    }

    // 解析推荐结果：后端返回 [{title, urls, reason}]
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
      items: enrichItems(rec?.outfit ?? rec?.urls ?? rec?.images ?? []),
    };

    app.setOutfitResult(outfitResult);
    emit('navigate', { page: 'outfit-result' });
  } catch (e) {
    console.error(e);
    ElMessage.error('搭配推荐失败，请检查网络后重试');
  } finally {
    loading.value = false;
    query.value = '';
  }
};

onMounted(() => {
  loadWeather();
  prefetchCloset();
});
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
.weather-card--flat {
  background: var(--m-card);
  color: var(--m-text);
  border: 1px solid var(--m-border);
  box-shadow: none;
}
.weather-main { display: flex; align-items: center; gap: 10px; }
.weather-icon { font-size: 32px; }
.weather-icon--dim { opacity: 0.7; }
.weather-temp { font-size: 36px; font-weight: 700; }
.weather-temp--dim { opacity: 0.7; }
.weather-meta { text-align: right; }
.weather-city { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.weather-desc { font-size: 12px; opacity: 0.9; }
.weather-status { display: none; }
.weather-retry {
  background: rgba(255,255,255,0.16);
  color: var(--m-primary);
  border: 1px solid var(--m-primary-light);
  border-radius: 999px;
  padding: 6px 16px;
  font-size: 13px;
  cursor: pointer;
}

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
.loading-state p { margin: 0 0 6px; }
.loading-hint { font-size: 12px; opacity: 0.8; }
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
