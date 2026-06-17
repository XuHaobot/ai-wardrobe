<template>
  <div class="role-selector-compact">
    <div 
      class="role-btn" 
      :class="{ active: currentRole === 'male' }"
      @click="switchRole('male')"
    >
      <span class="icon">♂</span>
      <span>Male</span>
    </div>
    
    <div 
      class="role-btn" 
      :class="{ active: currentRole === 'female' }"
      @click="switchRole('female')"
    >
      <span class="icon">♀</span>
      <span>Female</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['role-changed']);
const currentRole = ref('female');

const switchRole = (role) => {
  currentRole.value = role;
  emit('role-changed', role);
};
</script>

<style scoped>
.role-selector-compact {
  display: flex;
  gap: 8px;
  background: rgba(0,0,0,0.03);
  padding: 4px;
  border-radius: 12px;
  width: 100%;
}

.role-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
}

.role-btn:hover {
  background: rgba(255,255,255,0.5);
}

.role-btn.active {
  background: white;
  color: #000;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  font-weight: 600;
}

.icon {
  font-size: 14px;
}
</style>