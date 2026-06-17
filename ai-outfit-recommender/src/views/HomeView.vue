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
           </div>
           <UploadInput @uploaded="handleUploaded" />
        </div>
        <div class="workspace-body">
           <ClosetManager 
             ref="closetRef" 
             :highlighted-items="highlightedOutfitItems"
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
           <template v-else>
            <el-button size="small" round @click="$router.push('/login')">Login</el-button>
          </template>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import RoleManager from '../components/RoleManager.vue';
import OutfitDisplay from '../components/OutfitDisplay.vue';
import UploadInput from '../components/UploadInput.vue';
import WeatherWidget from '../components/WeatherWidget.vue';
import WeatherInput from '../components/WeatherInput.vue';
import ClosetManager from '../components/ClosetManager.vue';
import RecommendationList from '../components/RecommendationList.vue';
import ChatPanel from '../components/ChatPanel.vue';

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
</style>
