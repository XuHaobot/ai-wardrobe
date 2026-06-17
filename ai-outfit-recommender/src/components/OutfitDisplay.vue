<template>
  <div class="outfit-display-container">
    <!-- 试穿控制栏 -->
    <div class="stage-header">
      <h3 class="stage-title">Virtual Try-On</h3>
      <div class="header-actions">
        <el-button
          type="primary"
          size="small"
          round
          :loading="tryOnLoading"
          :disabled="!selectedItems.length"
          @click="doTryOn"
          class="tryon-btn"
        >
          <template v-if="tryOnLoading">
            AI 生成中...
          </template>
          <template v-else>
            ✨ 试穿 ({{ selectedItems.length }}件)
          </template>
        </el-button>
        <div v-if="generatedImageUrl" class="export-btn" @click="downloadGeneratedImage" title="下载图片">
          <el-icon><Download /></el-icon>
        </div>
      </div>
    </div>

    <!-- 已选衣物标签 -->
    <div class="selected-items-bar" v-if="selectedItems.length > 0 && !tryOnLoading">
      <span class="selected-label">已选:</span>
      <el-tag
        v-for="(item, idx) in selectedItems"
        :key="idx"
        size="small"
        closable
        @close="removeSelectedItem(idx)"
        class="item-tag"
      >
        {{ item.name || '衣物' + (idx+1) }}
      </el-tag>
    </div>

    <!-- 试穿画布 -->
    <div class="outfit-stage" ref="outfitStageRef">
      <!-- 加载状态 -->
      <div v-if="tryOnLoading" class="generating-state">
        <div class="spinner"></div>
        <p>AI 正在为你生成试穿效果...</p>
        <p class="sub-tip">首次生成可能需要 10~30 秒</p>
      </div>

      <!-- 已生成的试穿结果图 -->
      <img
        v-else-if="generatedImageUrl"
        :src="generatedImageUrl"
        alt="AI Try-On Result"
        class="result-image"
      />

      <!-- 模特底图（默认展示，含空状态提示） -->
      <div v-else class="model-stage">
        <img
          :src="baseRoleImage"
          :key="baseRoleImage"
          alt="Base Model"
          class="base-image"
        />
        <!-- 未选衣物时叠加提示 -->
        <div v-if="!currentOutfit.length && !(props.wardrobeSelection && props.wardrobeSelection.length)" class="empty-overlay">
          <p class="empty-tip">从衣橱中选择衣物，然后点击「试穿」按钮</p>
        </div>
      </div>

      <!-- 传统叠加模式（降级方案：选了衣物但无 AI 生成结果时） -->
      <template v-if="!generatedImageUrl && currentOutfit.length && !tryOnLoading">
        <img
          v-for="(item, index) in currentOutfit"
          :key="'layer-' + index"
          :src="item.imageUrl"
          :style="getItemStyle(item.category)"
          alt="Clothing Layer"
          class="clothing-layer"
        />
      </template>
    </div>

    <!-- 选择衣物弹窗 -->
    <el-dialog v-model="showItemPicker" title="选择要试穿的衣物" width="400px" class="picker-dialog">
      <div class="picker-grid">
        <div
          v-for="item in availableItems"
          :key="item.id"
          class="picker-item"
          :class="{ picked: isItemSelected(item) }"
          @click="toggleItemSelection(item)"
        >
          <el-image :src="item.imageUrl" fit="contain" class="picker-img" />
          <span class="picker-name">{{ item.name || '未命名' }}</span>
          <el-icon v-if="isItemSelected(item)" class="check-icon"><Check /></el-icon>
        </div>
      </div>
      <template #footer>
        <el-button @click="showItemPicker = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedItems.length" @click="confirmSelection">确定 ({{ selectedItems.length }}件)</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { Download, Check } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 属性定义
const props = defineProps({
  role: {
    type: String,
    default: 'female'
  },
  outfit: {
    type: Array,
    default: () => []
  },
  allClosetItems: {
    type: Array,
    default: () => []
  },
  wardrobeSelection: {
    type: Array,
    default: () => []
  }
});

const outfitStageRef = ref(null);
const currentRole = ref(props.role);
const currentOutfit = ref(props.outfit);

// ===== 虚拟试穿状态 =====
const tryOnLoading = ref(false);
const generatedImageUrl = ref('');
const showItemPicker = ref(false);
const selectedItems = ref([]);

// 可用衣物列表（来自父组件）
const availableItems = computed(() => props.allClosetItems || []);

// 监听父组件传来的角色和穿搭变化
watch(() => props.role, (newRole) => {
  currentRole.value = newRole;
  // 切换性别时清除已生成的结果
  generatedImageUrl.value = '';
});
watch(() => props.outfit, (newOutfit) => {
  currentOutfit.value = newOutfit;
});

// 同步衣橱手动选择到试穿列表
watch(() => props.wardrobeSelection, (newSelection) => {
  if (newSelection && newSelection.length) {
    selectedItems.value = newSelection.map(item => ({ ...item }));
  } else {
    selectedItems.value = [];
  }
}, { deep: true });

// 模特底图路径
const baseRoleImage = computed(() => {
  const fileName = props.role === 'male' ? '/uploads/男.png' : '/uploads/女.png';
  return fileName;
});

// 物品叠加样式(降级方案用)
const getItemStyle = (category) => {
  const zIndexMap = {
    coat: 10, hoodie: 5, long_sleeve: 4, short_sleeve: 3, pants: 2,
  };
  return { zIndex: zIndexMap[category] || 1 };
};

// ===== 衣物选择逻辑 =====
const isItemSelected = (item) => {
  return selectedItems.value.some(s => s.id === item.id);
};

const toggleItemSelection = (item) => {
  if (isItemSelected(item)) {
    selectedItems.value = selectedItems.value.filter(s => s.id !== item.id);
  } else {
    selectedItems.value.push({ ...item });
  }
};

const removeSelectedItem = (idx) => {
  selectedItems.value.splice(idx, 1);
};

const confirmSelection = () => {
  showItemPicker.value = false;
  // 自动执行试穿
  doTryOn();
};

// ===== 核心试穿API调用 =====
const doTryOn = async () => {
  // 如果没有选中的物品，使用当前outfit
  const itemsToTry = selectedItems.value.length > 0
    ? selectedItems.value
    : currentOutfit.value;

  if (!itemsToTry.length) {
    ElMessage.warning('请先选择要试穿的衣物');
    return;
  }

  tryOnLoading.value = true;
  generatedImageUrl.value = '';

  try {
    const clothingUrls = itemsToTry.map(i => i.imageUrl).filter(Boolean);

    // AI 异步生成可能需要较长时间，设置 180 秒超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);

    const res = await fetch('/tryon', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': localStorage.getItem('auth_token') || ''
      },
      body: JSON.stringify({
        gender: props.role,
        clothingUrls: clothingUrls
      }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const payload = await res.json();

    if (payload.code === 1 && payload.data) {
      const data = payload.data;
      if (data.success && data.imageUrl) {
        generatedImageUrl.value = data.imageUrl;
        ElMessage.success(data.message || '虚拟试穿成功！');
      } else {
        // 降级模式：显示模特底图+传统叠加
        ElMessage.warning(data.message || 'AI生图暂时不可用，使用基础展示');
        generatedImageUrl.value = '';
      }
    } else {
      ElMessage.error(payload.message || '试穿请求失败');
    }
  } catch (e) {
    console.error('[试穿] 错误:', e);
    if (e.name === 'AbortError') {
      ElMessage.warning('试穿请求超时，请重新选择衣物后重试');
    } else {
      ElMessage.error('试穿失败：' + (e.message || '请稍后重试'));
    }
  } finally {
    tryOnLoading.value = false;
  }
};

// 下载生成的图片
const downloadGeneratedImage = () => {
  if (!generatedImageUrl.value) return;

  // 如果是完整URL，直接下载
  if (generatedImageUrl.value.startsWith('http')) {
    const link = document.createElement('a');
    link.href = generatedImageUrl.value;
    link.download = `AI_Virtual_TryOn_${props.role}_${Date.now()}.png`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    ElMessage.success('图片下载中...');
    return;
  }

  // base64格式
  const link = document.createElement('a');
  link.href = generatedImageUrl.value;
  link.download = `AI_Virtual_TryOn_${Date.now()}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  ElMessage.success('图片已保存！');
};

// 暴露方法给父组件
defineExpose({ openItemPicker: () => { showItemPicker.value = true; }, doTryOn });
</script>

<style scoped>
.outfit-display-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.stage-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tryon-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-size: 12px;
  padding: 6px 14px;
}
.tryon-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: scale(1.02);
}
.tryon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.export-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.2s;
  color: #555;
}
.export-btn:hover {
  transform: scale(1.1);
  color: var(--accent-color);
}

/* 已选衣物标签 */
.selected-items-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  margin-bottom: 10px;
  background: rgba(102, 126, 234, 0.06);
  border-radius: 10px;
  flex-wrap: wrap;
}
.selected-label {
  font-size: 11px;
  color: #999;
  font-weight: 500;
}
.item-tag {
  max-width: 100px;
}
.item-tag .el-tag__content {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 试穿画布 */
.outfit-stage {
  flex: 1;
  position: relative;
  border-radius: 20px;
  background-color: #fafafa;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05);
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* AI加载动画 */
.generating-state {
  text-align: center;
  color: #667eea;
}
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(102,126,234,0.15);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.generating-state p {
  margin: 4px 0;
  font-size: 13px;
  font-weight: 500;
}
.sub-tip {
  font-size: 11px;
  color: #aaa;
  font-weight: 400;
}

/* 结果图 */
.result-image,
.base-image,
.clothing-layer {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

/* 模特底图容器 */
.model-stage {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.base-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: all 0.5s ease;
}

/* 空状态提示叠加在模特底图下方 */
.empty-overlay {
  position: absolute;
  bottom: -8px;
  left: 0;
  right: 0;
  text-align: center;
}
.empty-tip {
  font-size: 11px;
  color: #bbb;
  background: rgba(255,255,255,0.85);
  display: inline-block;
  padding: 4px 12px;
  border-radius: 8px;
}

.result-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}

.clothing-layer {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: auto;
  filter: drop-shadow(0 10px 20px rgba(0,0,0,0.15));
}

/* 衣物选择器 */
.picker-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  max-height: 350px;
  overflow-y: auto;
  padding: 4px;
}
.picker-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  background: #f5f5f7;
}
.picker-item:hover {
  border-color: #ddd;
}
.picker-item.picked {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
}
.picker-img {
  width: 100%;
  height: 70%;
  object-fit: contain;
}
.picker-name {
  display: block;
  text-align: center;
  font-size: 10px;
  color: #555;
  padding: 2px 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.check-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  color: #667eea;
  font-size: 14px;
  background: white;
  border-radius: 50%;
  padding: 2px;
}
</style>
