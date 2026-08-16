<template>
  <div class="mobile-app">
    <main class="mobile-main">
      <transition name="mfade" mode="out-in">
        <component
          :is="currentComponent"
          :key="currentPage"
          @navigate="handleNavigate"
          @back="handleBack"
          v-bind="pageProps"
        />
      </transition>
    </main>

    <!-- 底部 Tab Bar：仅主 Tab 页面显示 -->
    <nav v-if="isTabPage" class="mobile-tabbar">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        :class="['tab-item', { active: currentPage === tab.name }]"
        @click="switchTab(tab.name)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, provide, shallowRef } from 'vue';
import MobileAssistant from './MobileAssistant.vue';
import MobileWardrobe from './MobileWardrobe.vue';
import MobileTryOn from './MobileTryOn.vue';
import MobileItemDetail from './MobileItemDetail.vue';
import MobileUpload from './MobileUpload.vue';
import MobileOutfitResult from './MobileOutfitResult.vue';
import MobileLogin from './MobileLogin.vue';
import MobilePacking from './MobilePacking.vue';
import MobileHistory from './MobileHistory.vue';

const tabs = [
  { name: 'wardrobe', label: '衣橱', icon: '👗' },
  { name: 'tryon', label: '试穿', icon: '🎨' },
  { name: 'assistant', label: '助手', icon: '✨' },
];

// 页面组件映射
const pageComponents = {
  assistant: MobileAssistant,
  wardrobe: MobileWardrobe,
  tryon: MobileTryOn,
  'item-detail': MobileItemDetail,
  upload: MobileUpload,
  'outfit-result': MobileOutfitResult,
  login: MobileLogin,
  packing: MobilePacking,
  history: MobileHistory,
};

const currentPage = ref('assistant'); // 默认打开助手页
const pageHistory = ref([]); // 页面返回栈
const pageProps = ref({}); // 传递给子页面的 props

// 共享状态
const currentRole = ref('female');
const allClosetItems = ref([]);
const selectedItems = ref([]);
const currentItem = ref(null);
const currentOutfitResult = ref(null);

const isGuest = () => !localStorage.getItem('auth_token');
const authHeaders = () => {
  const token = localStorage.getItem('auth_token') || '';
  return token ? { Authorization: token } : { 'X-Guest': '1' };
};
const myOutfit = ref([]); // 用户自行添加的「我的搭配」单品

const isTabPage = computed(() => tabs.some(t => t.name === currentPage.value));
const currentComponent = computed(() => pageComponents[currentPage.value] || MobileAssistant);

const switchTab = (tabName) => {
  currentPage.value = tabName;
  pageHistory.value = [];
  pageProps.value = {};
};

const handleNavigate = ({ page, props = {}, replace = false }) => {
  if (!replace) {
    pageHistory.value.push({ page: currentPage.value, props: { ...pageProps.value } });
  }
  currentPage.value = page;
  pageProps.value = { ...props };
};

const handleBack = () => {
  const prev = pageHistory.value.pop();
  if (prev) {
    currentPage.value = prev.page;
    pageProps.value = prev.props || {};
  } else if (!isTabPage.value) {
    // 非 Tab 页面且无历史，回退到默认 Tab
    currentPage.value = 'assistant';
    pageProps.value = {};
  }
};

// 向子页面注入共享状态和方法
provide('mobileApp', {
  currentRole,
  allClosetItems,
  selectedItems,
  currentItem,
  currentOutfitResult,
  setRole: (role) => { currentRole.value = role; },
  setAllClosetItems: (items) => { allClosetItems.value = items; },
  setSelectedItems: (items) => { selectedItems.value = items; },
  setCurrentItem: (item) => { currentItem.value = item; },
  setOutfitResult: (result) => { currentOutfitResult.value = result; },
  isGuest,
  authHeaders,
  myOutfit,
  addToOutfit: (item) => {
    if (!myOutfit.value.some(i => i.id === item.id)) myOutfit.value = [...myOutfit.value, item];
  },
  removeFromOutfit: (item) => { myOutfit.value = myOutfit.value.filter(i => i.id !== item.id); },
  clearOutfit: () => { myOutfit.value = []; },
  navigate: handleNavigate,
  back: handleBack,
  switchTab,
});
</script>

<style scoped>
.mobile-app {
  min-height: 100vh;
  background: var(--m-bg);
  position: relative;
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
}

.mobile-main {
  min-height: 100vh;
}

.mobile-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(72px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  border-top: 1px solid var(--m-border);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
}

.tab-item {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--m-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  color: var(--m-primary);
}

.tab-icon {
  font-size: 22px;
  line-height: 1;
}

.tab-label {
  font-size: 11px;
  font-weight: 500;
}

.mfade-enter-active,
.mfade-leave-active {
  transition: opacity 0.18s ease;
}
.mfade-enter-from,
.mfade-leave-to {
  opacity: 0;
}
</style>
