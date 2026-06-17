<template>
  <div class="upload-wrapper">
    <el-upload
      class="custom-uploader"
      :show-file-list="false"
      :http-request="customUpload"
      :before-upload="beforeUpload"
      accept=".jpg,.jpeg,.png"
    >
      <el-button color="#000000" class="upload-btn" :loading="uploading">
        <el-icon class="el-icon--left"><Plus /></el-icon> Add New Item
      </el-button>
    </el-upload>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['uploaded']);
const uploading = ref(false);

const beforeUpload = (rawFile) => {
  const isImg = ['image/jpeg', 'image/png'].includes(rawFile.type);
  if (!isImg) {
    ElMessage.error('Please upload JPG or PNG images only.');
    return false;
  }
  return true;
};

const customUpload = async ({ file, onSuccess, onError }) => {
  uploading.value = true;

  try {
    const formData = new FormData();
    formData.append('image', file);

    const res = await fetch('/items', {
      method: 'POST',
      headers: {
        'Authorization': localStorage.getItem('auth_token') || ''
      },
      body: formData
    });

    if (!res.ok) {
      throw new Error('Upload failed');
    }

    ElMessage.success('Item added to closet');
    emit('uploaded');
    onSuccess?.();
  } catch (e) {
    console.error(e);
    ElMessage.error('Failed to upload item');
    onError?.(e);
  } finally {
    uploading.value = false;
  }
};
</script>

<style scoped>
.upload-btn {
  border-radius: 20px;
  font-weight: 500;
  padding: 8px 20px;
  transition: transform 0.2s;
}
.upload-btn:hover {
  transform: scale(1.05);
}
</style>
