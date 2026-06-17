<template>
  <div class="weather-widget">
    <div class="weather-header">
      <div class="weather-icon">{{ weatherIcon }}</div>
      <div class="weather-info">
        <div class="weather-temp">{{ weatherTemp }}</div>
        <div class="weather-desc">{{ weatherDesc }}</div>
      </div>
      <el-dropdown trigger="click" @command="selectCity">
        <span class="city-selector-btn">
          <el-icon><Location /></el-icon>
          {{ selectedCityName || '选择城市' }}
          <el-icon class="arrow"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu class="city-dropdown-menu">
            <div class="city-search-box">
              <el-input
                v-model="searchCity"
                placeholder="搜索城市..."
                size="small"
                clearable
                :prefix-icon="Search"
                @input="onSearchCity"
              />
            </div>
            <el-dropdown-item command="__auto_locate__">
              <span class="auto-locate-item">📍 自动定位</span>
            </el-dropdown-item>
            <template v-if="!searchCity">
              <!-- 热门城市 -->
              <div class="dropdown-section-label">热门城市</div>
              <el-dropdown-item
                v-for="c in hotCities"
                :key="c.value"
                :command="c.value"
              >
                <span :class="{ 'active-city': selectedCity === c.value }">{{ c.label }}</span>
              </el-dropdown-item>
            </template>
            <template v-else-if="filteredCities.length > 0">
              <el-dropdown-item
                v-for="c in filteredCities"
                :key="c.value"
                :command="c.value"
              >
                <span :class="{ 'active-city': selectedCity === c.value }">{{ c.label }}</span>
              </el-dropdown-item>
            </template>
            <template v-else-if="searchCity && filteredCities.length === 0">
              <div class="no-match-tip">无匹配城市，回车使用 "{{ searchCity }}" 查询</div>
              <el-dropdown-item :command="searchCity">
                使用「{{ searchCity }}」查询天气
              </el-dropdown-item>
            </template>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 手动输入框（备用） -->
    <div class="manual-input-row" v-if="showManualInput">
      <input
        ref="manualCityInput"
        v-model="manualCityText"
        placeholder="输入城市名..."
        @keyup.enter="confirmManualCity"
        @blur="cancelManualCity"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Location, ArrowDown, Search } from '@element-plus/icons-vue';

const props = defineProps({
  city: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['city-detected']);

const weatherIcon = ref('☀️');
const weatherTemp = ref('--°C');
const weatherDesc = ref('加载中...');
const selectedCity = ref('');
const selectedCityName = ref('');
const searchCity = ref('');
const showManualInput = ref(false);
const manualCityText = ref('');

// 热门城市列表
const hotCities = [
  { label: '北京', value: '北京' },
  { label: '上海', value: '上海' },
  { label: '广州', value: '广州' },
  { label: '深圳', value: '深圳' },
  { label: '杭州', value: '杭州' },
  { label: '成都', value: '成都' },
  { label: '武汉', value: '武汉' },
  { label: '南京', value: '南京' },
  { label: '西安', value: '西安' },
  { label: '重庆', value: '重庆' },
  { label: '长沙', value: '长沙' },
  { label: '天津', value: '天津' },
];

const allCities = hotCities;

const filteredCities = ref([]);

const onSearchCity = () => {
  if (!searchCity.value) {
    filteredCities.value = [];
    return;
  }
  const q = searchCity.value.trim().toLowerCase();
  filteredCities.value = allCities.filter(c =>
    c.label.toLowerCase().includes(q) || c.value.includes(q)
  );
};

const selectCity = (cmd) => {
  if (cmd === '__auto_locate__') {
    doAutoLocate();
  } else if (typeof cmd === 'string') {
    applyCity(cmd);
  }
};

const applyCity = (cityName) => {
  selectedCity.value = cityName;
  selectedCityName.value = cityName;
  localStorage.setItem('weather_city_selected', cityName);
  emit('city-detected', cityName);
  fetchWeather(cityName);
};

const doAutoLocate = () => {
  selectedCityName.value = '定位中...';

  // 先尝试浏览器定位，同时启动超时保底
  let settled = false;
  const timeoutId = setTimeout(() => {
    if (!settled) {
      settled = true;
      console.warn('[定位] 浏览器定位超时，尝试 IP 定位');
      ipLocate();
    }
  }, 6000);

  if (!navigator.geolocation) {
    clearTimeout(timeoutId);
    settled = true;
    ipLocate();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      const { latitude, longitude } = position.coords;
      reverseGeocode(longitude, latitude);
    },
    (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      console.warn('[定位] 浏览器定位失败:', err.message, '，尝试 IP 定位');
      ipLocate();
    },
    { timeout: 5000, enableHighAccuracy: false }
  );
};

/**
 * IP 定位（降级方案）：通过后端代理获取大致城市
 * 高德 API Key 仅存在于后端 .env，前端 bundle 不会暴露
 */
const ipLocate = async () => {
  try {
    const res = await fetch('/api/locate/ip');
    const payload = await res.json();
    if (payload.code === 1 && payload.data) {
      const { adcode, province, city } = payload.data;
      if (city && typeof city === 'string' && city !== '[]') {
        const cleanCity = city.replace(/市$/, '');
        applyCity(cleanCity);
        return;
      }
      // 有 adcode 但没城市名，直接用 adcode 查后端
      selectedCityName.value = province || '未知';
      selectedCity.value = adcode;
      emit('city-detected', adcode);
      fetchWeather(adcode);
      return;
    } else {
      console.warn('[IP定位] 后端返回失败:', payload.message);
    }
  } catch (e) {
    console.warn('[IP定位] 失败:', e);
  }
  // 所有定位方式都失败，回退北京
  fallbackDefault();
};

const fallbackDefault = () => {
  selectedCityName.value = '北京';
  selectedCity.value = '北京';
  emit('city-detected', '北京');
  fetchWeather('北京');
};

const reverseGeocode = async (lng, lat) => {
  try {
    const res = await fetch(`/api/locate/regeo?lng=${lng}&lat=${lat}`);
    const payload = await res.json();
    if (payload.code === 1 && payload.data) {
      const { adcode, province, city } = payload.data;
      let cityName = '';
      if (city && city !== [] && typeof city === 'string') {
        cityName = city.replace(/市$/, '');
      }
      if (!cityName && province && typeof province === 'string') {
        cityName = province.replace(/市$/, '').replace(/省$/, '');
      }
      if (cityName) {
        applyCity(cityName);
        return;
      }
    } else {
      console.warn('[逆地理编码] 后端返回失败:', payload.message);
    }
  } catch (e) {
    console.warn('[逆地理编码] 失败:', e);
  }
  // 逆地理编码失败，降级到 IP 定位
  ipLocate();
};

const confirmManualCity = () => {
  if (manualCityText.value.trim()) {
    applyCity(manualCityText.value.trim());
  }
  showManualInput.value = false;
};

const cancelManualCity = () => {
  showManualInput.value = false;
};

const fetchWeather = async (city) => {
  try {
    const res = await fetch(`/weather?city=${encodeURIComponent(city)}`);
    const payload = await res.json();
    if (payload.code === 1 && payload.data) {
      const text = payload.data;
      const tempMatch = text.match(/温度：(\d+)/);
      const weatherMatch = text.match(/天气：(\S+?)，/);
      weatherTemp.value = tempMatch ? `${tempMatch[1]}°C` : '--°C';
      // 只显示天气状况，不再重复城市名（城市已在右侧下拉按钮中显示）
      const w = weatherMatch ? weatherMatch[1] : '';
      weatherDesc.value = w || '未知';
      // 根据天气设置图标
      if (w.includes('晴')) weatherIcon.value = '☀️';
      else if (w.includes('云') || w.includes('阴')) weatherIcon.value = '⛅';
      else if (w.includes('雨')) weatherIcon.value = '🌧️';
      else if (w.includes('雪')) weatherIcon.value = '❄️';
      else weatherIcon.value = '🌤️';
    } else {
      weatherDesc.value = '未知';
      weatherTemp.value = '--°C';
    }
  } catch (e) {
    console.error('[天气] 获取失败:', e);
    weatherDesc.value = '离线模式';
    weatherTemp.value = '--°C';
  }
};

onMounted(() => {
  // 优先级: 传入的city prop > 用户手动选过的城市 > 自动定位
  const savedSelected = localStorage.getItem('weather_city_selected');
  if (props.city && props.city.trim()) {
    applyCity(props.city.trim());
  } else if (savedSelected) {
    applyCity(savedSelected);
  } else {
    doAutoLocate();
  }
});
</script>

<style scoped>
.weather-widget {
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  padding: 14px;
  border-radius: 16px;
  color: white;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(255, 154, 158, 0.3);
}

.weather-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weather-icon {
  font-size: 22px;
}
.weather-temp {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}
.weather-desc {
  font-size: 11px;
  opacity: 0.9;
  margin-top: 2px;
}

.city-selector-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 12px;
  background: rgba(255,255,255,0.25);
  cursor: pointer;
  font-size: 11px;
  transition: background 0.2s;
  white-space: nowrap;
}
.city-selector-btn:hover {
  background: rgba(255,255,255,0.35);
}
.arrow {
  font-size: 10px;
}

/* Dropdown styles */
.city-dropdown-menu {
  width: 220px !important;
  padding: 4px !important;
}
.city-search-box {
  padding: 4px 8px;
}
.dropdown-section-label {
  font-size: 11px;
  color: #999;
  padding: 6px 16px 2px;
  font-weight: 600;
}
.auto-locate-item {
  color: var(--el-color-primary);
  font-weight: 500;
}
.active-city {
  color: var(--el-color-primary);
  font-weight: 600;
}
.no-match-tip {
  font-size: 11px;
  color: #aaa;
  padding: 8px 16px;
  text-align: center;
}

.manual-input-row {
  display: flex;
  align-items: center;
}
.manual-input-row input {
  border: none;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  width: 100%;
  outline: none;
  box-sizing: border-box;
}
</style>
