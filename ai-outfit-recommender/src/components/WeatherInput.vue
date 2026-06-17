<template>
  <div class="weather-bar">
    <div class="input-wrapper">
      <el-icon class="search-icon"><Search /></el-icon>
      <input 
        v-model="purpose" 
        class="custom-input" 
        placeholder="今天要去哪里？（如：约会、健身）" 
        @keyup.enter="getOutfitRecommendation"
      />
    </div>
    <el-button 
      type="primary" 
      circle 
      :loading="recommending" 
      @click="getOutfitRecommendation"
      class="action-btn"
    >
      <el-icon v-if="!recommending"><MagicStick /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { MagicStick, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  city: {
    type: String,
    default: ''
  }
});

const recommending = ref(false);
const purpose = ref('');

const emit = defineEmits(['recommend-trigger']);

const getOutfitRecommendation = async () => {
  recommending.value = true;
  await new Promise(resolve => setTimeout(resolve, 1500));
  recommending.value = false;
  ElMessage.success('正在为你生成穿搭推荐...');
  emit('recommend-trigger', { purpose: purpose.value.trim(), city: props.city || '' });
};
</script>

<style scoped>
.weather-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  padding: 4px 6px 4px 12px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  transition: all 0.3s;
  width: 100%;
}

.weather-bar:focus-within {
  border-color: var(--accent-color);
  box-shadow: 0 4px 10px rgba(0, 113, 227, 0.1);
}

.input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.search-icon {
  color: #86868b;
  font-size: 14px;
}

.custom-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: #1d1d1f;
  width: 100%;
  font-family: inherit;
}
.custom-input::placeholder {
  color: #86868b;
}

.action-btn {
  width: 28px;
  height: 28px;
  min-width: 28px;
  font-size: 14px;
}
</style>
