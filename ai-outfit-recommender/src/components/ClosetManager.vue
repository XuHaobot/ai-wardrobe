<template>
  <div class="closet-container">
    <!-- Category Filter Tabs -->
    <div class="category-tabs">
      <div
        v-for="cat in allCategories"
        :key="cat.value"
        class="tab-item"
        :class="{ active: activeCategory === cat.value }"
        @click="activeCategory = cat.value"
      >
        {{ cat.label }}
      </div>

      <!-- 添加分类按钮 -->
      <button class="tab-item tab-add-btn" @click.stop="showAddCategoryDialog = true" title="添加新分类">
        <el-icon><Plus /></el-icon>
      </button>
    </div>

    <div class="closet-content">
      <el-skeleton :rows="4" animated v-if="loading" />
      <template v-else>
        <div class="closet-grid" v-if="filteredItems.length > 0">
          <div
            class="closet-card"
            :class="{ 'card-selected': isSelected(item) }"
            v-for="item in filteredItems"
            :key="item.id"
          >
            <div class="image-wrapper">
              <el-image
                :src="item.imageUrl"
                fit="contain"
                loading="lazy"
                class="item-img"
              />
              <!-- 选择勾选区域 -->
              <div class="select-check" @click.stop="toggleSelect(item, $event)">
                <el-icon v-if="isSelected(item)" class="check-icon"><Check /></el-icon>
              </div>
              <!-- 衣物名称标签 -->
              <span v-if="item.name" class="item-name-tag">{{ item.name }}</span>
              <div class="hover-overlay">
                <button class="action-btn edit-name-btn" @click.stop="openEditName(item)" title="修改名称">
                  <el-icon><EditPen /></el-icon>
                </button>
                <el-popconfirm title="确认删除?" @confirm="handleDelete(item)">
                  <template #reference>
                    <button class="action-btn delete-btn" @click.stop>
                      <el-icon><Delete /></el-icon>
                    </button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-closet" v-else>
          <div class="empty-icon">📦</div>
          <p>该分类下暂无衣物</p>
        </div>
      </template>
    </div>

    <!-- 选中衣物操作栏 -->
    <div class="selection-bar" v-if="selectedClosetItems.length > 0">
      <span class="sel-count">已选 {{ selectedClosetItems.length }} 件</span>
      <div class="sel-actions">
        <el-button size="small" text @click="clearSelection">清除</el-button>
        <el-button size="small" type="primary" round @click="tryOnSelected">
          试穿选中
        </el-button>
      </div>
    </div>

    <div class="panel-details">
      <span class="count-label">{{ filteredItems.length }} Items</span>
    </div>

    <!-- 详情对话框（含编辑名称） -->
    <el-dialog v-model="detailVisible" width="380px" class="item-dialog" :show-close="false">
      <div class="dialog-content">
        <el-image :src="currentItem.imageUrl" fit="contain" class="dialog-image" />
        <div class="dialog-details">
          <!-- 可编辑名称 -->
          <div class="name-edit-row" v-if="editingName">
            <el-input
              ref="editNameInput"
              v-model="editingNameText"
              size="small"
              placeholder="输入衣物名称"
              @keyup.enter="saveName"
              @keyup.escape="cancelEditName"
            >
              <template #append>
                <el-button size="small" type="primary" @click="saveName">保存</el-button>
              </template>
            </el-input>
          </div>
          <h4 v-else class="editable-title" @dblclick="startEditName">
            {{ currentItem.name || 'Untitled Item' }}
            <el-icon class="edit-pen-small"><EditPen /></el-icon>
          </h4>
          <p class="tag">{{ getCategoryLabel(currentItem.category || 'all') }}</p>
          <p class="date">Added on {{ formatDate(currentItem.uploadDate) }}</p>
        </div>
      </div>
    </el-dialog>

    <!-- 添加分类对话框 -->
    <el-dialog v-model="showAddCategoryDialog" width="320px" title="添加自定义分类" :show-close="false">
      <div class="add-cat-body">
        <el-input
          v-model="newCategoryName"
          placeholder="输入分类名称（如：连衣裙、运动鞋...）"
          size="large"
          @keyup.enter="confirmAddCategory"
        />
      </div>
      <template #footer>
        <el-button @click="showAddCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddCategory" :disabled="!newCategoryName.trim()">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { Delete, EditPen, Plus, Check } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['count-update', 'category-changed', 'items-loaded', 'selection-changed', 'try-on']);

const props = defineProps({
  highlightedItems: {
    type: Array,
    default: () => []
  }
});

const loading = ref(true);
const detailVisible = ref(false);
const currentItem = ref({});
const activeCategory = ref('all');

// ===== 自定义分类管理 =====
const DEFAULT_CATEGORIES = [
  { value: 'all', label: '全部' },
  { value: 'short_sleeve', label: '短袖' },
  { value: 'long_sleeve', label: '长袖' },
  { value: 'hoodie', label: '卫衣' },
  { value: 'pants', label: '裤子' },
  { value: 'coat', label: '棉服' },
  { value: 'sneakers', label: '运动鞋' },
  { value: 'shoes', label: '鞋靴' },
  { value: 'dress', label: '连衣裙' },
  { value: 'accessories', label: '配饰' },
];

// 从 localStorage 读取用户自定义分类
const loadCustomCategories = () => {
  try {
    const raw = localStorage.getItem('custom_categories');
    if (raw) return JSON.parse(raw);
  } catch (e) {
    // ignore parse error
  }
  return [];
};

const customCategories = ref(loadCustomCategories());
const showAddCategoryDialog = ref(false);
const newCategoryName = ref('');

const allCategories = computed(() => {
  return [...DEFAULT_CATEGORIES, ...customCategories.value];
});

// 自动发现衣物中的新分类（后端返回的未知分类自动加入标签列表）
const autoDiscoverCategories = (items) => {
  const knownValues = new Set([
    ...DEFAULT_CATEGORIES.map(c => c.value),
    ...customCategories.value.map(c => c.value)
  ]);
  const discovered = [];
  for (const item of items) {
    const cat = item.category;
    if (cat && cat !== 'all' && !knownValues.has(cat)) {
      knownValues.add(cat);
      // 用分类原始值作为显示名称（首字母大写）
      const label = cat.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());
      discovered.push({ value: cat, label });
    }
  }
  if (discovered.length) {
    customCategories.value = [...customCategories.value, ...discovered];
    localStorage.setItem('custom_categories', JSON.stringify(customCategories.value));
    emit('category-changed', customCategories.value);
  }
};

const confirmAddCategory = () => {
  const name = newCategoryName.value.trim();
  if (!name) return;
  // 检查重复
  if (customCategories.value.some(c => c.label === name)) {
    ElMessage.warning('该分类已存在');
    return;
  }
  const value = 'custom_' + Date.now();
  const newCat = { value, label: name };
  customCategories.value.push(newCat);
  localStorage.setItem('custom_categories', JSON.stringify(customCategories.value));
  emit('category-changed', customCategories.value);
  ElMessage.success(`分类「${name}」已添加`);
  newCategoryName.value = '';
  showAddCategoryDialog.value = false;
};

// 删除自定义分类（仅限自定义的）
const removeCustomCategory = (value) => {
  if (!value.startsWith('custom_')) return;
  customCategories.value = customCategories.value.filter(c => c.value !== value);
  localStorage.setItem('custom_categories', JSON.stringify(customCategories.value));
  emit('category-changed', customCategories.value);
  if (activeCategory.value === value) activeCategory.value = 'all';
};

// ===== 编辑衣物名称 =====
const editingName = ref(false);
const editingNameText = ref('');
const editNameInput = ref(null);

const startEditName = () => {
  editingName.value = true;
  editingNameText.value = currentItem.value.name || '';
  nextTick(() => {
    editNameInput.value?.focus();
  });
};

const cancelEditName = () => {
  editingName.value = false;
  editingNameText.value = '';
};

const saveName = async () => {
  const newName = editingNameText.value.trim();
  try {
    const res = await fetch('/closet/items/name', {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentItem.value.id, name: newName })
    });
    if (res.ok) {
      currentItem.value.name = newName;
      // 同步更新列表中的数据
      const item = closetItems.value.find(x => x.id === currentItem.value.id);
      if (item) item.name = newName;
      ElMessage.success('名称已更新');
    } else {
      ElMessage.error('更新失败');
    }
  } catch (e) {
    ElMessage.error('网络错误');
  } finally {
    editingName.value = false;
    editingNameText.value = '';
  }
};

// 从卡片上的编辑按钮打开编辑
const openEditName = (item) => {
  currentItem.value = item;
  detailVisible.value = true;
  nextTick(() => startEditName());
};

// ===== 衣橱数据 =====
const closetItems = ref([]);

// ===== 多选状态 =====
const selectedClosetItems = ref([]);

const isSelected = (item) => {
  return selectedClosetItems.value.some(s => s.id === item.id);
};

// 当推荐的高亮变化时，自动选中匹配的衣物（按 ID 或图片 URL 匹配）
watch(() => props.highlightedItems, (newItems) => {
  if (!newItems || !newItems.length) return;
  // 替换而非累积：先清空旧选中，再添加新推荐匹配项
  selectedClosetItems.value = [];
  newItems.forEach(hi => {
    const item = closetItems.value.find(c =>
      String(c.id) === String(hi.id) ||
      (c.imageUrl && hi.imageUrl && c.imageUrl === hi.imageUrl)
    );
    if (item) {
      selectedClosetItems.value.push({ ...item });
    }
  });
  emit('selection-changed', [...selectedClosetItems.value]);
}, { immediate: true });

// 手动选择/取消选择
const toggleSelect = (item, event) => {
  if (event) event.stopPropagation();
  if (isSelected(item)) {
    selectedClosetItems.value = selectedClosetItems.value.filter(s => s.id !== item.id);
  } else {
    selectedClosetItems.value.push({ ...item });
  }
  emit('selection-changed', [...selectedClosetItems.value]);
};

const clearSelection = () => {
  selectedClosetItems.value = [];
  emit('selection-changed', []);
};

const tryOnSelected = () => {
  if (!selectedClosetItems.value.length) return;
  emit('try-on', [...selectedClosetItems.value]);
};

const getCategoryLabel = (c) => {
  // 先在所有分类中查找
  const found = allCategories.value.find(cat => cat.value === c);
  if (found) return found.label;
  return '未分类';
};

const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token') || '';
  return token ? { Authorization: token } : {};
};

const normalizeCategory = (category, description = '') => {
  const rawCategory = String(category || '').trim();

  // 先检查是否是自定义分类
  if (rawCategory && rawCategory.startsWith('custom_')) return rawCategory;
  if (customCategories.value.some(c => c.value === rawCategory)) return rawCategory;

  const knownCategories = ['short_sleeve', 'long_sleeve', 'hoodie', 'pants', 'coat', 'sneakers', 'shoes', 'dress', 'accessories', 'all'];
  if (knownCategories.includes(rawCategory)) {
    return rawCategory;
  }

  const source = `${rawCategory}\n${description || ''}`.toLowerCase();

  if (/(牛仔裤|运动裤|休闲裤|长裤|短裤|裤子|裤|pants|jeans|trousers|shorts)/i.test(source)) {
    return 'pants';
  }
  if (/(卫衣|连帽衫|连帽卫衣|hoodie|sweatshirt)/i.test(source)) {
    return 'hoodie';
  }
  if (/(棉服|棉衣|羽绒服|羽绒|大衣|夹克|外套|coat|jacket|parka|down)/i.test(source)) {
    return 'coat';
  }
  if (/(运动鞋|球鞋|跑鞋|板鞋|sneakers|sneaker|trainers)/i.test(source)) {
    return 'sneakers';
  }
  if (/(皮鞋|高跟鞋|靴子|凉鞋|拖鞋|单鞋|乐福鞋|shoes|shoe|boots|heels|sandals|loafers)/i.test(source)) {
    return 'shoes';
  }
  if (/(连衣裙|裙子|半身裙|短裙|长裙|dress|skirt)/i.test(source)) {
    return 'dress';
  }
  if (/(袜子|腰带|帽子|围巾|手套|包|socks|belt|hat|scarf|gloves|bag)/i.test(source)) {
    return 'accessories';
  }
  if (/(短袖|t恤|t-shirt|tee|polo|短袖上衣)/i.test(source)) {
    return 'short_sleeve';
  }
  if (/(长袖|衬衫|针织衫|毛衣|长袖上衣|上衣|shirt|sweater|knit)/i.test(source)) {
    return 'long_sleeve';
  }

  // 尝试匹配自定义分类标签
  for (const cat of customCategories.value) {
    if (source.includes(cat.label.toLowerCase())) return cat.value;
  }

  // 保留后端返回的分类值（非空且长度合理时），否则归入"全部"
  if (rawCategory && rawCategory !== 'all' && rawCategory.length <= 20) {
    return rawCategory;
  }

  return 'all';
};

const mapItems = (arr) =>
  (Array.isArray(arr) ? arr : []).map(d => ({
    id: d.id ?? Math.random(),
    name: d.name ?? '',
    imageUrl: d.url ?? d.imageUrl ?? '',
    category: normalizeCategory(d.category, d.description),
    description: d.description ?? '',
    uploadDate: d.uploadDate ?? ''
  })).filter(x => x.imageUrl);

const extractItems = (pageData) => {
  if (Array.isArray(pageData)) return pageData;
  return pageData?.items ?? pageData?.list ?? pageData?.records ?? pageData?.rows ?? [];
};

const filteredItems = computed(() => {
  if (activeCategory.value === 'all') return closetItems.value;
  return closetItems.value.filter(i => i.category === activeCategory.value);
});

const formatDate = (dateStr) => {
  if (!dateStr) return '未知日期';
  try {
    return new Date(dateStr).toLocaleDateString();
  } catch {
    return dateStr;
  }
};

const fetchClosetData = async (options = {}) => {
  loading.value = true;
  if (options.resetCategory) {
    activeCategory.value = 'all';
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`/closet/items?page=1&size=1000`, {
      headers: getAuthHeaders(),
      signal: controller.signal
    });
    if (res.ok) {
      const payload = await res.json();
      const pageData = payload?.data ?? payload?.result ?? payload;
      const list = extractItems(pageData);

      closetItems.value = mapItems(list);
      autoDiscoverCategories(closetItems.value);
      emit('count-update', closetItems.value.length);
      emit('items-loaded', [...closetItems.value]); // 传递副本供试穿使用
    } else if (res.status === 401) {
      console.warn('[ClosetManager] 认证失败');
    } else {
      console.warn('[ClosetManager] 加载失败:', res.status);
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      console.warn('[ClosetManager] 请求超时(8s)');
    } else {
      console.warn('[ClosetManager] 网络异常:', err);
    }
  } finally {
    clearTimeout(timer);
    loading.value = false;
  }
};

const viewItemDetail = (item) => {
  currentItem.value = item;
  editingName.value = false; // 重置编辑状态
  selectedClosetItems.value = [];
  emit('selection-changed', []);
};

const handleDelete = async (item) => {
  try {
    const url = item.imageUrl || '';
    if (!url) return;
    const res = await fetch(`/closet/items?url=${encodeURIComponent(url)}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      closetItems.value = closetItems.value.filter(x => x.imageUrl !== url);
      emit('count-update', closetItems.value.length);
      ElMessage.success('已删除');
    } else {
      ElMessage.error('删除失败');
    }
  } catch {
    ElMessage.error('删除错误');
  }
};

onMounted(() => {
  fetchClosetData();
});

defineExpose({ fetchClosetData });
</script>

<style scoped>
.closet-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.category-tabs {
  display: flex;
  gap: 6px;
  padding: 0 4px 14px;
  border-bottom: 1px solid rgba(0,0,0,0.03);
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.tab-item {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  background: rgba(0,0,0,0.03);
  color: #86868b;
  transition: all 0.2s;
}
.tab-item.active {
  background: #1d1d1f;
  color: white;
}
.tab-item:hover:not(.active) {
  background: rgba(0,0,0,0.06);
}
.tab-add-btn {
  min-width: auto;
  padding: 6px 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #86868b;
}
.tab-add-btn:hover {
  background: rgba(0,113,227,0.08);
  color: #0071e3;
}

.closet-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.closet-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.closet-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  aspect-ratio: 1;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  border: 1px solid rgba(0,0,0,0.02);
}
.closet-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.06);
}
.closet-card.card-selected {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
  background: rgba(102, 126, 234, 0.04);
}

/* 选择勾选框 */
.select-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.12);
  background: rgba(255,255,255,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 3;
  transition: all 0.2s;
  opacity: 0;
}
.closet-card:hover .select-check,
.closet-card.card-selected .select-check {
  opacity: 1;
}
.select-check:hover {
  border-color: #667eea;
  transform: scale(1.1);
}
.card-selected .select-check {
  background: #667eea;
  border-color: #667eea;
}
.check-icon {
  color: white;
  font-size: 12px;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.item-img {
  width: 100%;
  height: 100%;
}

/* 衣物名称标签 */
.item-name-tag {
  position: absolute;
  bottom: 2px;
  left: 4px;
  right: 4px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 4px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  z-index: 1;
}

.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 2;
}
.closet-card:hover .hover-overlay {
  opacity: 1;
}

.action-btn {
  background: white;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 13px;
}
.edit-name-btn {
  color: #0071e3;
}
.delete-btn {
  color: #ff3b30;
}

.empty-closet {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #86868b;
  opacity: 0.6;
}
.empty-icon { font-size: 32px; margin-bottom: 8px; }

.panel-details {
  font-size: 12px;
  color: #86868b;
  text-align: right;
  padding-top: 10px;
}

/* Dialog */
.dialog-content { text-align: center; }
.dialog-image { background: #f5f5f7; border-radius: 12px; padding: 20px; margin-bottom: 16px; }

/* 可编辑标题 */
.editable-title {
  margin: 0 0 4px 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s;
}
.editable-title:hover {
  color: #0071e3;
}
.edit-pen-small {
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s;
}
.editable-title:hover .edit-pen-small {
  opacity: 1;
}

.name-edit-row {
  margin-bottom: 10px;
}

.dialog-details .tag { font-size: 12px; background: #eee; display: inline-block; padding: 2px 8px; border-radius: 4px; margin-bottom: 4px; }
.dialog-details .date { color: #aaa; font-size: 12px; }

/* Add category dialog */
.add-cat-body {
  padding: 10px 0;
}

/* 选中衣物操作栏 */
.selection-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-radius: 10px;
  margin-top: 10px;
}
.sel-count {
  font-size: 13px;
  color: #667eea;
  font-weight: 600;
}
.sel-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}
</style>
