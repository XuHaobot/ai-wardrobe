<template>
  <div class="m-page detail-page">
    <header class="page-header">
      <button class="m-back-btn" @click="emit('back')">←</button>
      <h1 class="m-page-title">衣物详情</h1>
      <button class="m-back-btn" @click="showMenu = !showMenu">⋯</button>
    </header>

    <div class="guest-banner" v-if="isGuest">
      <span>✨</span>
      <span>游客模式下仅可预览，登录后可管理标签与删除衣物</span>
    </div>

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
        <div class="section-head">
          <h3 class="section-label">风格标签</h3>
          <span v-if="tagChanged" class="changed-hint">已修改，记得保存</span>
        </div>

        <div class="style-tags">
          <span v-for="(tag, idx) in tags" :key="tag + idx" class="style-tag">
            {{ tag }}
            <button v-if="!isGuest" class="tag-del" @click="removeTag(idx)">×</button>
          </span>
          <span v-if="tags.length === 0" class="empty-tag">暂无标签</span>
        </div>

        <div v-if="!isGuest" class="tag-input-row">
          <input
            v-model="newTag"
            class="m-input tag-input"
            placeholder="输入标签，如：通勤、复古、运动"
            maxlength="12"
            @keyup.enter="addTag"
          />
          <button class="m-btn-primary tag-add" @click="addTag" :disabled="!newTag.trim()">添加</button>
        </div>

        <button v-if="!isGuest && tagChanged" class="save-tags" @click="saveTags" :disabled="savingTags">
          {{ savingTags ? '保存中…' : '保存标签' }}
        </button>
      </div>
    </div>

    <button v-if="!isGuest" class="delete-btn" @click="confirmDelete">
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
import { computed, inject, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate', 'back']);
const app = inject('mobileApp');

const item = computed(() => app.currentItem.value);
const isGuest = computed(() => app.isGuest());

const showDeleteConfirm = ref(false);
const showMenu = ref(false);
const tags = ref([]);
const newTag = ref('');
const savingTags = ref(false);
const originalTags = ref([]);

const parseTags = (raw) => {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw.filter(Boolean);
  return raw.split(',').map(t => t.trim()).filter(Boolean);
};

watch(() => item.value, (it) => {
  const list = parseTags(it?.style);
  tags.value = [...list];
  originalTags.value = [...list];
}, { immediate: true });

const tagChanged = computed(() =>
  tags.value.length !== originalTags.value.length ||
  tags.value.some((t, i) => t !== originalTags.value[i])
);

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

const addTag = () => {
  const t = newTag.value.trim();
  if (!t) return;
  if (tags.value.includes(t)) {
    ElMessage.warning('标签已存在');
    return;
  }
  tags.value.push(t);
  newTag.value = '';
};
const removeTag = (idx) => { tags.value.splice(idx, 1); };

const saveTags = async () => {
  if (!item.value?.id) return;
  savingTags.value = true;
  try {
    const res = await fetch('/closet/items/tags', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...app.authHeaders()
      },
      body: JSON.stringify({ id: item.value.id, tags: tags.value })
    });
    const payload = await res.json();
    if (res.ok && payload.code === 1) {
      ElMessage.success('标签已保存');
      originalTags.value = [...tags.value];
      // 同步本地缓存，返回衣橱时列表能反映
      app.setCurrentItem({ ...item.value, style: tags.value.join(',') });
    } else {
      ElMessage.error(payload.msg || '保存失败');
    }
  } catch {
    ElMessage.error('保存失败');
  } finally {
    savingTags.value = false;
  }
};

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
      headers: app.authHeaders()
    });
    if (res.ok) {
      ElMessage.success('已删除');
      emit('back');
    } else {
      const payload = await res.json().catch(() => ({}));
      ElMessage.error(payload.detail || payload.msg || '删除失败');
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

.detail-image-card {
  background: #FFFFFF;
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
  object-fit: contain;
  padding: 8px;
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
  margin-bottom: 20px;
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

.style-section { margin-top: 4px; }
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-label {
  font-size: 13px;
  color: var(--m-text-secondary);
  margin: 0;
}
.changed-hint {
  font-size: 12px;
  color: var(--m-primary);
}
.style-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.style-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  color: var(--m-primary);
  background: var(--m-primary-light);
}
.empty-tag { font-size: 13px; color: var(--m-text-secondary); }
.tag-del {
  background: transparent;
  border: none;
  color: var(--m-primary);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}
.tag-input-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
.tag-input { flex: 1; }
.tag-add { padding: 12px 18px; font-size: 14px; }
.save-tags {
  width: 100%;
  padding: 12px;
  border-radius: var(--m-radius-md);
  border: none;
  background: var(--m-dark);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
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
