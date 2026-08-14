<template>
  <div class="app-root">
    <div class="studio-container">
      <!-- 1. Left Sidebar: AI Control -->
      <aside class="sidebar-left glass-panel">
        <div class="sidebar-header">
          <div class="brand">
            <span class="logo-icon">✨</span>
            <span class="brand-text">AI Stylist</span>
          </div>
        </div>

        <div class="sidebar-content">
          <div class="weather-widget mb-4">
             <WeatherWidget :city="currentCity" @city-detected="onCityDetected" />
          </div>

          <!-- Tab 切换：推荐 / 对话 -->
          <div class="sidebar-tabs">
            <button
              :class="['tab-btn', { active: sidebarTab === 'recommend' }]"
              @click="sidebarTab = 'recommend'"
            >推荐</button>
            <button
              :class="['tab-btn', { active: sidebarTab === 'chat' }]"
              @click="sidebarTab = 'chat'"
            >AI 对话</button>
          </div>

          <!-- 推荐面板 -->
          <div v-show="sidebarTab === 'recommend'" class="ai-section">
             <div class="section-label">AI Assistant</div>
             <div class="weather-box mb-3">
               <WeatherInput :city="currentCity" @recommend-trigger="handleRecommendationTrigger" />
             </div>
             <RecommendationList 
               :trigger="recommendTriggerKey" 
               :purpose="recommendPurpose" 
               :city="currentCity"
               @apply-outfit="handleApplyOutfit" 
             />
          </div>

          <!-- Chat 对话面板 -->
          <div v-show="sidebarTab === 'chat'" class="chat-section">
            <ChatPanel />
          </div>
        </div>
      </aside>

      <!-- 2. Center: Wardrobe (Main Workspace) -->
      <main class="workspace-center glass-panel">
        <div class="workspace-header">
           <div class="header-left">
             <h3>My Wardrobe</h3>
             <span class="badge">{{ totalClosetItems }}</span>
             <span v-if="isGuest" class="guest-badge" title="游客试玩模式：仅可体验，数据不保存">✨ 游客</span>
           </div>
           <div class="header-actions">
             <button class="header-btn" @click="openPacking" title="旅行打包助手">
               <el-icon><Promotion /></el-icon> 旅行打包
             </button>
             <button class="header-btn" @click="showHistory = true" title="我的搭配历史">
               <el-icon><Collection /></el-icon> 我的搭配
             </button>
             <UploadInput v-if="!isGuest" @uploaded="handleUploaded" />
             <el-tooltip v-else content="登录后可上传自己的衣物" placement="bottom">
               <button class="header-btn disabled" disabled>＋ 上传</button>
             </el-tooltip>
           </div>
        </div>
        <div class="workspace-body">
            <ClosetManager 
              ref="closetRef" 
              :highlighted-items="highlightedOutfitItems"
              :readonly="isGuest"
              @count-update="val => totalClosetItems = val" 
              @items-loaded="onClosetItemsLoaded"
              @selection-changed="onWardrobeSelection"
              @try-on="handleWardrobeTryOn"
            />
        </div>
      </main>

      <!-- 3. Right Sidebar: Visual Try-On -->
      <aside class="sidebar-right glass-panel">
        <div class="visual-header">
          <h3>Virtual Try-On</h3>
        </div>
        <div class="visual-body">
          <div class="role-selector mb-3">
             <RoleManager @role-changed="handleRoleChange" />
          </div>
          <div class="stage-wrapper">
             <OutfitDisplay
               ref="outfitDisplayRef"
               :role="currentRole"
               :outfit="currentOutfit"
               :all-closet-items="allClosetItems"
               :wardrobe-selection="wardrobeSelection"
             />
          </div>
        </div>
        
        <div class="user-footer">
          <template v-if="isLoggedIn">
             <div class="user-info">
               <el-avatar :size="24" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
               <span class="username">Designer</span>
             </div>
             <el-button link type="danger" size="small" @click="logout">Exit</el-button>
          </template>
          <template v-else-if="isGuest">
             <span class="guest-tag">游客试玩模式</span>
             <el-button size="small" round type="primary" @click="handleLogout">登录 / 注册</el-button>
          </template>
          <template v-else>
            <el-button size="small" round @click="$router.push('/login')">Login</el-button>
          </template>
        </div>
      </aside>
    </div>

    <!-- 搭配历史侧滑面板 -->
    <transition name="slide">
      <div v-if="showHistory" class="history-drawer-mask" @click.self="showHistory = false">
        <div class="history-drawer">
          <HistoryPanel @close="showHistory = false" />
        </div>
      </div>
    </transition>

    <!-- 旅行打包助手 -->
    <PackingDialog ref="packingRef" />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { Promotion, Collection } from '@element-plus/icons-vue';
import RoleManager from '../components/RoleManager.vue';
import OutfitDisplay from '../components/OutfitDisplay.vue';
import UploadInput from '../components/UploadInput.vue';
import WeatherWidget from '../components/WeatherWidget.vue';
import WeatherInput from '../components/WeatherInput.vue';
import ClosetManager from '../components/ClosetManager.vue';
import RecommendationList from '../components/RecommendationList.vue';
import ChatPanel from '../components/ChatPanel.vue';
import HistoryPanel from '../components/HistoryPanel.vue';
import PackingDialog from '../components/PackingDialog.vue';

// State
const currentRole = ref('female');
const currentOutfit = ref([]);
const recommendTriggerKey = ref(0);
const recommendPurpose = ref('');
const isLoggedIn = ref(!!localStorage.getItem('auth_token'));
const totalClosetItems = ref(0);
const closetRef = ref(null);
const outfitDisplayRef = ref(null);
const currentCity = ref(''); // 当前定位城市
const allClosetItems = ref([]); // 所有衣橱物品，供试穿选择使用
const highlightedOutfitItems = ref([]); // 推荐衣物完整数据（用于衣橱高亮匹配）
const wardrobeSelection = ref([]); // 衣橱手动选中的衣物
const sidebarTab = ref('recommend'); // 左侧栏tab：recommend / chat

const router = useRouter();

// 游客试玩模式：无登录且 guest_mode 开启时为游客
const isGuest = ref(!localStorage.getItem('auth_token') && localStorage.getItem('guest_mode') === '1');
const showHistory = ref(false);
const packingRef = ref(null);

const openPacking = () => packingRef.value?.open();
const handleLogout = () => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('guest_mode');
  isGuest.value = false;
  router.push('/login');
};

// Actions
const handleRoleChange = (newRole) => {
  currentRole.value = newRole;
  currentOutfit.value = [];
};

const handleRecommendationTrigger = ({ purpose }) => {
  recommendPurpose.value = purpose;
  recommendTriggerKey.value = Date.now();
};

const handleApplyOutfit = (outfitItems) => {
  // 将推荐衣物映射到衣橱中的实际物品（按 imageUrl 匹配）
  const matchedItems = outfitItems.map(recItem => {
    const url = recItem.imageUrl || recItem.url || '';
    return allClosetItems.value.find(c => c.imageUrl === url) || null;
  }).filter(Boolean);

  highlightedOutfitItems.value = outfitItems;

  // 清除旧的叠加层
  currentOutfit.value = [];

  if (matchedItems.length > 0) {
    // 走"已选标签"模式，和衣橱手动选择一样的效果
    wardrobeSelection.value = matchedItems;
  } else {
    // 推荐衣物不在衣橱中，回退使用原始数据
    wardrobeSelection.value = outfitItems.filter(i => i.imageUrl).map(i => ({
      id: i.id ?? Math.random(),
      name: i.name || '推荐衣物',
      imageUrl: i.imageUrl
    }));
  }
};

const handleUploaded = () => {
  if (closetRef.value) {
    closetRef.value.fetchClosetData({ resetCategory: true });
  }
};

const onCityDetected = (city) => {
  currentCity.value = city || '';
};

const onClosetItemsLoaded = (items) => {
  allClosetItems.value = items;
};

const onWardrobeSelection = (items) => {
  wardrobeSelection.value = items;
};

const handleWardrobeTryOn = (items) => {
  currentOutfit.value = items;
  // 触发试穿面板的试穿动作
  nextTick(() => {
    outfitDisplayRef.value?.doTryOn?.();
  });
};

const logout = () => {
  localStorage.removeItem('auth_token');
  isLoggedIn.value = false;
  router.push('/login');
};
</script>

<style scoped>
.app-root {
  height: 100vh;
  width: 100vw;
  background: radial-gradient(circle at 50% 10%, #ffffff 0%, #f0f2f5 100%);
  color: #1d1d1f;
  overflow: hidden;
  padding: 16px;
  box-sizing: border-box; /* Ensure padding includes in 100vh */
}

.studio-container {
  display: flex;
  height: 100%;
  gap: 16px;
  width: 100%; /* Full Width */
  /* max-width removed */
}

/* Glass Panel */
.glass-panel {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 1. Left Sidebar */
.sidebar-left {
  width: 300px;
  min-width: 300px;
  padding: 24px;
}

.sidebar-header {
  margin-bottom: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
}

/* Weather Widget wrapper spacing */
.weather-widget {
  /* Only handles margin — inner styles are in WeatherWidget.vue */
}

.section-label {
  font-size: 12px;
  text-transform: uppercase;
  color: #86868b;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.mb-3 { margin-bottom: 16px; }
.mb-4 { margin-bottom: 24px; }

/* 2. Center Workspace */
.workspace-center {
  flex: 1; /* Grows to fill space */
  min-width: 0; /* Prevents flex items from overflowing container */
}

.workspace-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-left h3 { margin: 0; font-size: 18px; }
.badge {
  background: #1d1d1f;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}
.guest-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid rgba(0,0,0,0.12);
  background: #fff;
  color: #1d1d1f;
  border-radius: 18px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.header-btn:hover { border-color: #667eea; color: #667eea; }
.header-btn.disabled { opacity: 0.5; cursor: not-allowed; }
.guest-tag { font-size: 12px; color: #667eea; font-weight: 500; }

/* History drawer */
.history-drawer-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.25);
  display: flex; justify-content: flex-end; z-index: 100;
}
.history-drawer {
  width: 380px; max-width: 90vw; height: 100%;
  background: #fff; padding: 20px; box-sizing: border-box;
  box-shadow: -4px 0 24px rgba(0,0,0,0.08);
}
.slide-enter-active, .slide-leave-active { transition: opacity 0.25s; }
.slide-enter-from, .slide-leave-to { opacity: 0; }

.workspace-body {
  flex: 1;
  overflow: hidden;
  padding: 20px 24px;
}


/* 3. Right Sidebar */
.sidebar-right {
  width: 380px;
  min-width: 380px;
  display: flex;
  flex-direction: column;
}

.visual-header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.visual-header h3 { margin: 0; font-size: 16px; }

.visual-body {
  flex: 1;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.stage-wrapper {
  flex: 1;
  /* Ensure stage takes available space */
  display: flex;
  flex-direction: column;
  min-height: 0; 
}
/* Ensure RoleManager container doesn't take too much space */
.role-selector {
  margin-bottom: 12px;
}


.user-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(0,0,0,0.04);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.4);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  font-size: 13px;
  font-weight: 500;
}

/* Sidebar Tabs */
.sidebar-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  padding: 3px;
}

.tab-btn {
  flex: 1;
  padding: 6px 0;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #86868b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: white;
  color: #1d1d1f;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.tab-btn:not(.active):hover {
  color: #1d1d1f;
}

/* Chat section takes remaining space */
.chat-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* Make sidebar-content flex to allow chat to grow */
.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
}

/* ============================================================
   移动端 H5 适配 (max-width: 768px)
   三栏桌面布局 → 单列可滚动；顺序：衣橱 → 试穿 → AI助手
   ============================================================ */
@media (max-width: 768px) {
  .app-root {
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  .studio-container {
    flex-direction: column;
    height: auto;
    overflow: visible;
    gap: 12px;
    padding: 12px;
  }

  /* 三栏全宽，重排顺序 */
  .sidebar-left,
  .workspace-center,
  .sidebar-right {
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }
  .workspace-center { order: 1; }   /* 衣橱优先：进去即可选衣物 */
  .sidebar-right    { order: 2; }   /* 虚拟试穿 */
  .sidebar-left     { order: 3; }   /* AI 推荐/对话最后 */

  /* 取消内部独立滚动，交还给页面滚动 */
  .sidebar-content { overflow-y: visible; }
  .workspace-body { overflow: visible; padding: 14px; }

  /* 顶栏换行，按钮可触达 */
  .workspace-header {
    flex-wrap: wrap;
    gap: 8px;
    padding: 14px 16px;
  }
  .header-actions {
    flex-wrap: wrap;
    width: 100%;
    justify-content: flex-start;
  }
  .header-btn { font-size: 12px; padding: 6px 10px; }

  /* 试穿区给足高度，避免被压扁 */
  .sidebar-right .visual-body {
    min-height: 62vh;
  }
  .stage-wrapper { min-height: 320px; }

  /* AI 助手区让聊天/推荐自然撑开 */
  .sidebar-left { padding: 16px; }
  .chat-section { min-height: 60vh; }

  /* 搭配历史抽屉在手机上全屏 */
  .history-drawer {
    width: 100%;
    max-width: 100%;
  }
}

/* 子组件移动端微调（穿透 scoped） */
@media (max-width: 768px) {
  /* 衣橱网格在窄屏降到 3 列 */
  .workspace-body :deep(.closet-grid) {
    grid-template-columns: repeat(3, 1fr);
  }
  /* 试穿舞台图片自适应不溢出 */
  .stage-wrapper :deep(img) {
    max-width: 100%;
    height: auto;
  }
}
</style>
