<template>
  <div class="m-page detail-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">衣物详情</h1>
      <button class="m-back-btn" @click="showMenu = !showMenu">⋯</button>
    </header>

    <div class="detail-image-card">
      <img v-if="item?.imageUrl" :src="item.imageUrl" :alt="item.name" />
    </div>

    <div class="detail-body">
      <h2 class="item-name">{{ item?.name || '未命名衣物' }}</h2>
      <div class="meta-row">
        <span class="meta-chip">分类 {{ categoryLabel }}</span>
        <span class="meta-chip color-chip">
          <span class="color-dot" :style="{ background: itemColor }"></span>
          颜色 {{ item?.color || '未知' }}
        </span>
      </div>

      <div class="style-section">
        <h3 class="section-label">风格标签</h3>
        <div class="style-tags">
          <span v-for="tag in styleTags" :key="tag" class="style-tag">{{ tag }}</span>
        </div>
      </div>
    </div>

    <button class="delete-btn" @click="confirmDelete">
      <span>🗑</span>
      <span>删除这件衣物</span>
    </button>

    <!-- 底部操作 -->
    <div class="detail-footer">
      <button class="m-btn-ghost" @click="emit('back')">返回</button>
      <button class="m-btn-primary" @click="addToTryOn">加入试穿</button>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteConfirm" class="confirm-mask" @click.self="showDeleteConfirm = false">
      <div class="confirm-card">
        <p class="confirm-title">确认删除？</p>
        <p class="confirm-tip">删除后无法恢复</p>
        <div class="confirm-actions">
          <button class="m-btn-ghost" @click="showDeleteConfirm = false">取消</button>
          <button class="m-btn-primary" @click="doDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const item = computed(() => app.currentItem.value);
const showDeleteConfirm = ref(false);
const showMenu = ref(false);

const categoryMap = {
  short_sleeve: '短袖', long_sleeve: '长袖', hoodie: '卫衣', pants: '裤子',
  coat: '外套', sneakers: '运动鞋', shoes: '鞋靴', dress: '连衣裙', accessories: '配饰'
};
const categoryLabel = computed(() => categoryMap[item.value?.category] || item.value?.category || '未分类');
const itemColor = computed(() => {
  const c = item.value?.color || '';
  if (/深绿|绿/.test(c)) return '#166534';
  if (/黑/.test(c)) return '#111827';
  if (/红/.test(c)) return '#DC2626';
  if (/蓝/.test(c)) return '#2563EB';
  if (/白/.test(c)) return '#F3F4F6';
  return '#9CA3AF';
});
const styleTags = computed(() => {
  const raw = item.value?.style || item.value?.description || '';
  if (Array.isArray(raw)) return raw.slice(0, 5);
  return ['休闲', '百搭', '夏日'];
});

const addToTryOn = () => {
  if (!item.value) return;
  const current = app.selectedItems.value;
  if (current.some(i => i.id === item.value.id)) {
    ElMessage.info('这件衣物已在试穿列表');
  } else {
    app.setSelectedItems([...current, item.value]);
    ElMessage.success('已加入试穿列表');
  }
};

const confirmDelete = () => { showDeleteConfirm.value = true; };

const doDelete = async () => {
  if (!item.value?.imageUrl) return;
  try {
    const res = await fetch(`/closet/items?url=${encodeURIComponent(item.value.imageUrl)}`, {
      method: 'DELETE',
      headers: { Authorization: localStorage.getItem('auth_token') || '' }
    });
    if (res.ok) {
      ElMessage.success('已删除');
      emit('back');
    } else {
      ElMessage.error('删除失败');
    }
  } catch {
    ElMessage.error('删除错误');
  } finally {
    showDeleteConfirm.value = false;
  }
};
</script>

<style scoped>
.detail-page { padding-top: 12px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-image-card {
  background: #E5E7EB;
  border-radius: var(--m-radius-xl);
  aspect-ratio: 1 / 1;
  overflow: hidden;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.detail-image-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-body {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 16px;
  margin-bottom: 12px;
}
.item-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--m-text);
  margin: 0 0 14px;
}
.meta-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--m-border);
  border-radius: var(--m-radius-md);
  font-size: 13px;
  color: var(--m-text);
}
.color-chip { gap: 8px; }
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.1);
}

.style-section { margin-top: 8px; }
.section-label {
  font-size: 13px;
  color: var(--m-text-secondary);
  margin: 0 0 10px;
}
.style-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.style-tag {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  color: var(--m-primary);
  background: var(--m-primary-light);
}

.delete-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  background: #FEF2F2;
  color: #DC2626;
  border: none;
  border-radius: var(--m-radius-lg);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 16px;
}

.detail-footer {
  display: flex;
  gap: 12px;
}
.detail-footer button { flex: 1; }

.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.confirm-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 20px;
  width: 280px;
  text-align: center;
}
.confirm-title { font-size: 16px; font-weight: 600; margin: 0 0 6px; }
.confirm-tip { font-size: 13px; color: var(--m-text-secondary); margin: 0 0 16px; }
.confirm-actions { display: flex; gap: 10px; }
.confirm-actions button { flex: 1; }
</style>
