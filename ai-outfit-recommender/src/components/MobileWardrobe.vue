<template>
  <div class="m-page wardrobe-page">
    <!-- Header -->
    <header class="wardrobe-header">
      <div class="title-row">
        <h1 class="m-page-title">My Wardrobe</h1>
        <span class="count-badge">{{ items.length }}</span>
        <span v-if="isGuest" class="guest-badge">✨ 游客</span>
      </div>

      <div class="quick-actions">
        <button class="quick-btn" @click="goPacking">
          <span class="icon">✈️</span>
          <span>旅行打包</span>
        </button>
        <button class="quick-btn" @click="goHistory">
          <span class="icon">😌</span>
          <span>我的搭配</span>
        </button>
        <button class="quick-btn" @click="goUpload" :disabled="isGuest">
          <span class="icon">+</span>
          <span>上传</span>
        </button>
      </div>
    </header>

    <!-- Category filter -->
    <div class="category-row">
      <button
        v-for="cat in categories"
        :key="cat.value"
        :class="['m-chip', { active: activeCategory === cat.value }]"
        @click="activeCategory = cat.value"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Items grid -->
    <div class="items-grid">
      <div
        v-for="item in filteredItems"
        :key="item.id"
        :class="['item-card', { selected: isSelected(item) }]"
      >
        <div class="img-wrap" @click.stop="toggleSelect(item, $event)">
          <img :src="item.imageUrl" :alt="item.name" />
          <div v-if="isSelected(item)" class="check-dot">✓</div>
          <button class="detail-dot" @click.stop="handleCardClick(item)">⋯</button>
        </div>
        <p class="item-name">{{ item.name }}</p>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && filteredItems.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <p>该分类下暂无衣物</p>
    </div>

    <!-- Bottom selection bar -->
    <div v-if="selected.length > 0" class="selection-bar">
      <div class="sel-info">
        <div class="sel-count">已选 {{ selected.length }} 件</div>
        <button class="sel-clear" @click="clearSelection">清除</button>
      </div>
      <button class="m-btn-primary tryon-btn" @click="tryOnSelected">
        <span>✨</span>
        <span>试穿选中</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['navigate']);
const app = inject('mobileApp');

const categories = [
  { value: 'all', label: '全部' },
  { value: 'short_sleeve', label: '短袖' },
  { value: 'long_sleeve', label: '长袖' },
  { value: 'hoodie', label: '卫衣' },
  { value: 'pants', label: '裤子' },
];

const items = ref([]);
const loading = ref(true);
const activeCategory = ref('all');
const selected = ref([]);

const isGuest = computed(() => !localStorage.getItem('auth_token') && localStorage.getItem('guest_mode') === '1');

const filteredItems = computed(() => {
  if (activeCategory.value === 'all') return items.value;
  return items.value.filter(i => i.category === activeCategory.value);
});

const isSelected = (item) => selected.value.some(s => s.id === item.id);

const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token') || '';
  return token ? { Authorization: token } : {};
};

const normalizeCategory = (category, description = '') => {
  const raw = String(category || '').trim().toLowerCase();
  const source = `${raw}\n${description || ''}`.toLowerCase();
  if (/(牛仔裤|运动裤|休闲裤|长裤|短裤|裤子|裤|pants|jeans|trousers|shorts)/i.test(source)) return 'pants';
  if (/(卫衣|连帽衫|hoodie|sweatshirt)/i.test(source)) return 'hoodie';
  if (/(棉服|棉衣|羽绒服|大衣|夹克|外套|coat|jacket|parka|down)/i.test(source)) return 'coat';
  if (/(运动鞋|球鞋|跑鞋|板鞋|sneakers|sneaker|trainers)/i.test(source)) return 'sneakers';
  if (/(皮鞋|高跟鞋|靴子|凉鞋|拖鞋|单鞋|乐福鞋|shoes|shoe|boots|heels|sandals|loafers)/i.test(source)) return 'shoes';
  if (/(连衣裙|裙子|半身裙|短裙|长裙|dress|skirt)/i.test(source)) return 'dress';
  if (/(袜子|腰带|帽子|围巾|手套|包|socks|belt|hat|scarf|gloves|bag)/i.test(source)) return 'accessories';
  if (/(短袖|t恤|t-shirt|tee|polo)/i.test(source)) return 'short_sleeve';
  if (/(长袖|衬衫|针织衫|毛衣|上衣|shirt|sweater|knit)/i.test(source)) return 'long_sleeve';
  return raw && raw !== 'all' ? raw : 'all';
};

const mapItems = (arr) => (Array.isArray(arr) ? arr : []).map(d => ({
  id: d.id ?? Math.random(),
  name: d.name ?? '',
  imageUrl: d.url ?? d.imageUrl ?? '',
  category: normalizeCategory(d.category, d.description),
  description: d.description ?? '',
  color: d.color ?? '',
  style: d.style ?? '',
  uploadDate: d.uploadDate ?? ''
})).filter(x => x.imageUrl);

const fetchItems = async () => {
  loading.value = true;
  try {
    const res = await fetch('/closet/items?page=1&size=1000', { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('加载失败');
    const payload = await res.json();
    const list = payload?.data ?? payload?.result ?? payload;
    items.value = mapItems(Array.isArray(list) ? list : (list?.items ?? []));
    app.setAllClosetItems(items.value);
  } catch (e) {
    console.error(e);
    ElMessage.error('衣橱加载失败');
  } finally {
    loading.value = false;
  }
};

const handleCardClick = (item) => {
  app.setCurrentItem(item);
  emit('navigate', { page: 'item-detail' });
};

const toggleSelect = (item, event) => {
  event.stopPropagation();
  if (isSelected(item)) {
    selected.value = selected.value.filter(s => s.id !== item.id);
  } else {
    selected.value.push(item);
  }
};

const clearSelection = () => { selected.value = []; };

const tryOnSelected = () => {
  app.setSelectedItems([...selected.value]);
  emit('navigate', { page: 'tryon' });
};

const goPacking = () => emit('navigate', { page: 'packing' });
const goHistory = () => emit('navigate', { page: 'history' });
const goUpload = () => {
  if (isGuest.value) {
    ElMessage.warning('登录后可上传自己的衣物');
    return;
  }
  emit('navigate', { page: 'upload' });
};

onMounted(fetchItems);
</script>

<style scoped>
.wardrobe-page {
  padding-top: 12px;
}

.wardrobe-header {
  margin-bottom: 16px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.count-badge {
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--m-dark);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guest-badge {
  margin-left: auto;
  font-size: 12px;
  color: var(--m-primary);
  background: var(--m-primary-light);
  padding: 4px 10px;
  border-radius: 999px;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.quick-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 0;
  background: var(--m-card);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--m-text);
  cursor: pointer;
}
.quick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.quick-btn .icon {
  font-size: 16px;
}

.category-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 16px;
  scrollbar-width: none;
}
.category-row::-webkit-scrollbar { display: none; }

.items-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding-bottom: 100px;
}

.item-card {
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 12px;
  border: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}
.item-card.selected {
  border-color: var(--m-primary);
}

.img-wrap {
  aspect-ratio: 1;
  background: #E5E7EB;
  border-radius: var(--m-radius-md);
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.check-dot {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--m-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.detail-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  border: none;
  color: var(--m-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
}

.item-name {
  margin: 10px 0 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--m-text);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--m-text-secondary);
}
.empty-icon { font-size: 40px; margin-bottom: 10px; }

.selection-bar {
  position: fixed;
  bottom: calc(72px + env(safe-area-inset-bottom, 0px));
  left: 16px;
  right: 16px;
  background: var(--m-card);
  border-radius: var(--m-radius-lg);
  padding: 12px 16px;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 90;
}

.sel-info { display: flex; flex-direction: column; }
.sel-count { font-size: 15px; font-weight: 600; color: var(--m-text); }
.sel-clear { font-size: 12px; color: var(--m-text-secondary); background: transparent; border: none; padding: 0; text-align: left; cursor: pointer; }

.tryon-btn {
  padding: 10px 18px;
  font-size: 14px;
}
</style>
