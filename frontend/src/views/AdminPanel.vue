<template>
  <div class="admin-panel" v-if="isLoggedIn">
    <!-- Header -->
    <header class="admin-header">
      <div class="header-left">
        <h1 class="admin-title">⚙️ 管理后台</h1>
        <span class="admin-badge">时空修复图鉴</span>
      </div>
      <div class="header-right">
        <router-link to="/" class="back-link">← 返回前台</router-link>
      </div>
    </header>

    <!-- Engine Health Section -->
    <section class="admin-section">
      <h2 class="section-title">📊 算法引擎探针</h2>
      <div class="health-cards">
        <div class="health-card">
          <div class="health-icon">🧠</div>
          <div class="health-info">
            <div class="health-label">YOLOv8 引擎状态</div>
            <div class="health-value" :class="healthData.yolo_loaded ? 'ok' : 'pending'">
              {{ healthData.yolo_loaded ? '已加载 / Warmup完成' : '未加载 / 异常' }}
            </div>
          </div>
        </div>
        <div class="health-card">
          <div class="health-icon">💾</div>
          <div class="health-info">
            <div class="health-label">大模型显存/内存占用</div>
            <div class="health-value" v-if="healthData.psutil_available">
              {{ healthData.ram_usage_percent }}%
              <div class="progress-bar"><div class="progress-fill" :style="{ width: healthData.ram_usage_percent + '%' }"></div></div>
            </div>
            <div class="health-value pending" v-else>探针未安装</div>
          </div>
        </div>
        <div class="health-card">
          <div class="health-icon">⚡</div>
          <div class="health-info">
            <div class="health-label">算力基座负载 (CPU)</div>
            <div class="health-value" v-if="healthData.psutil_available">
              {{ healthData.cpu_usage_percent }}%
              <div class="progress-bar"><div class="progress-fill warning" :style="{ width: healthData.cpu_usage_percent + '%' }"></div></div>
            </div>
            <div class="health-value pending" v-else>探针未安装</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Mode Toggle Section -->
    <section class="admin-section">
      <h2 class="section-title">🎛️ 运行模式</h2>
      <div class="mode-toggle-card">
        <div class="mode-info">
          <div class="mode-label">当前模式</div>
          <div class="mode-value" :class="mode">
            {{ mode === 'preset' ? '🎭 预设演示' : '🔬 真实演算' }}
          </div>
          <p class="mode-desc" v-if="mode === 'preset'">
            降噪和超分使用预存图片 + 精美动画模拟，快速流畅。YOLO 识别仍为真实算法。
          </p>
          <p class="mode-desc" v-else>
            降噪（TK_CBM3D）和超分（Real-ESRGAN）调用真实后端算法处理，耗时较长。
          </p>
        </div>
        <button class="mode-switch-btn" @click="toggleMode" :disabled="switching">
          {{ switching ? '切换中...' : (mode === 'preset' ? '切换为真实演算' : '切换为预设演示') }}
        </button>
      </div>
    </section>

    <!-- Gallery Management Section -->
    <section class="admin-section">
      <div class="section-header">
        <h2 class="section-title">🖼️ 画廊管理 <span class="count-badge">{{ gallery.length }} 幅</span></h2>
        
        <div class="header-actions">
          <button class="batch-btn ok" @click="batchRestore(true)" :disabled="uploading" title="一键点亮所有图鉴">✨ 一键全亮</button>
          <button class="batch-btn dim" @click="batchRestore(false)" :disabled="uploading" title="一键熄灭所有图鉴">🌑 一键全灭</button>
          <input type="file" ref="fileInput" @change="onFileSelected" accept="image/*" style="display: none" />
          <button class="upload-btn" @click="triggerUpload" :disabled="uploading">
            {{ uploading ? '上传并生成预设中...' : '➕ 添加新画作' }}
          </button>
        </div>
      </div>
      
      <div class="gallery-grid">
        <div class="gallery-admin-card" v-for="item in gallery" :key="item.id">
          <div class="card-preview">
            <img :src="'/gallery/' + item.filename" class="preview-img" :alt="item.title" />
            <div class="card-id">#{{ item.id }}</div>
          </div>
          <div class="card-info">
            <input class="card-title-input" v-model="item.title" @blur="saveGallery(item)" placeholder="标题" />
            <input class="card-desc-input" v-model="item.desc" @blur="saveGallery(item)" placeholder="描述" />
            <div class="card-meta">
              <span class="card-filename">📄 {{ item.filename }}</span>
              <button 
                class="status-toggle-btn" 
                :class="{ active: item.isRestored }"
                @click="toggleItemStatus(item)"
                :title="item.isRestored ? '点击熄灭此画作' : '点击点亮此画作'"
              >
                {{ item.isRestored ? '✨ 已点亮' : '🌑 未点亮' }}
              </button>
            </div>
          </div>
          <div class="card-variants" v-if="item.variants">
            <div class="variant-row">
              <span class="variant-label">原图</span>
              <span class="variant-status" :class="item.variants.original ? 'ok' : 'missing'">
                {{ item.variants.original ? '✓' : '✗' }}
              </span>
            </div>
            <div class="variant-row">
              <span class="variant-label">受损版</span>
              <span class="variant-status" :class="item.variants.damaged ? 'ok' : 'missing'">
                {{ item.variants.damaged ? '✓' : '✗' }}
              </span>
            </div>
            <div class="variant-row">
              <span class="variant-label">降噪版</span>
              <span class="variant-status" :class="item.variants.purified ? 'ok' : 'missing'">
                {{ item.variants.purified ? '✓' : '✗' }}
              </span>
            </div>
          </div>
          <!-- Show warning if any variant is missing -->
          <div class="variant-warning" v-if="item.variants && (!item.variants.original || !item.variants.damaged || !item.variants.purified)">
            ⚠️ 缺失预设文件
          </div>
          <button class="delete-btn" @click="deleteItem(item.id)" title="删除此唐卡">🗑️</button>
        </div>
      </div>
    </section>
  </div>

  <!-- Login Screen -->
  <div class="admin-login" v-else>
    <div class="login-card">
      <div class="login-icon">🔐</div>
      <h2 class="login-title">管理员验证</h2>
      <p class="login-desc">请输入管理密码以访问后台</p>
      <input
        class="login-input"
        type="password"
        v-model="passwordInput"
        @keyup.enter="doLogin"
        placeholder="管理密码"
        autofocus
      />
      <button class="login-btn" @click="doLogin" :disabled="!passwordInput">
        验证并进入
      </button>
      <p class="login-error" v-if="loginError">{{ loginError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API = 'http://127.0.0.1:8000'

const isLoggedIn = ref(false)
const passwordInput = ref('')
const loginError = ref('')
const adminPassword = ref('')

const mode = ref('preset')
const switching = ref(false)
const gallery = ref([])
const fileInput = ref(null)
const uploading = ref(false)

const healthData = ref({
  yolo_loaded: false,
  ram_usage_percent: 0,
  cpu_usage_percent: 0,
  psutil_available: false
})
let healthInterval = null

// --- Login ---
const doLogin = async () => {
  loginError.value = ''
  adminPassword.value = passwordInput.value
  try {
    const res = await axios.get(`${API}/api/v1/admin/settings`, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    mode.value = res.data.mode
    isLoggedIn.value = true
    // 登录后加载数据
    await loadGallery()
    await loadHealth()
    healthInterval = setInterval(loadHealth, 3000)
  } catch (e) {
    if (e.response?.status === 401) {
      loginError.value = '密码错误，请重试'
    } else {
      loginError.value = '无法连接后端服务'
    }
  }
}

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})

// --- Load Health ---
const loadHealth = async () => {
  if (!isLoggedIn.value) return; // 不要再未登录时轮询
  
  try {
    const res = await axios.get(`${API}/api/v1/admin/health`, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    healthData.value = res.data
  } catch (e) {
    if (e.response?.status === 401) {
      // 密码失效或未登录，立刻停止轮询并退回登录页
      if (healthInterval) {
        clearInterval(healthInterval)
        healthInterval = null
      }
      isLoggedIn.value = false
    }
  }
}

// --- Load Gallery ---
const loadGallery = async () => {
  try {
    const res = await axios.get(`${API}/api/v1/admin/gallery`, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    gallery.value = res.data.gallery
  } catch (e) {
    console.error('加载画廊失败', e)
  }
}

// --- Mode Toggle ---
const toggleMode = async () => {
  switching.value = true
  const newMode = mode.value === 'preset' ? 'real' : 'preset'
  try {
    await axios.put(`${API}/api/v1/admin/settings?mode=${newMode}`, null, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    mode.value = newMode
  } catch (e) {
    console.error('模式切换失败', e)
  }
  switching.value = false
}

// --- Upload New Artwork ---
const triggerUpload = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const onFileSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post(`${API}/api/v1/admin/upload`, formData, {
      headers: { 
        'X-Admin-Password': adminPassword.value,
        'Content-Type': 'multipart/form-data'
      }
    })
    ElMessage.success('上传成功！预设管线正在后台自动生成中...')
    await loadGallery()
  } catch (e) {
    console.error('上传失败', e)
    ElMessage.error(e.response?.data?.detail || '上传失败，检查后端日志')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = '' // reset
  }
}

// --- Save & Update Status ---
const saveGallery = async (item) => {
  try {
    await axios.put(`${API}/api/v1/admin/gallery/${item.id}`, {
      title: item.title,
      desc: item.desc,
      isRestored: item.isRestored || false
    }, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    ElMessage.success('保存成功')
  } catch (e) {
    console.error('保存失败', e)
    ElMessage.error('保存失败')
  }
}

// --- Toggle Item Status ---
const toggleItemStatus = async (item) => {
  item.isRestored = !item.isRestored
  await saveGallery(item)
  
  // Admin action explicitly overrides local player progress
  try {
    const state = JSON.parse(localStorage.getItem('thangka_restored_state') || '{}')
    if (state[item.id] !== undefined) {
      delete state[item.id]
      localStorage.setItem('thangka_restored_state', JSON.stringify(state))
    }
  } catch (e) {}
}

// --- Batch Restore ---
const batchRestore = async (status) => {
  try {
    await axios.put(`${API}/api/v1/admin/gallery/batch-restore`, { isRestored: status }, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    
    // Clear all local player progress to ensure the backend truth is fully respected
    localStorage.removeItem('thangka_restored_state')
    
    ElMessage.success(`已成功一键${status ? '点亮' : '熄灭'}所有画作！`)
    await loadGallery()
  } catch (e) {
    console.error('批量更新状态失败', e)
    ElMessage.error('批量更新状态失败')
  }
}

// --- Delete Item ---
const deleteItem = async (id) => {
  if (!confirm('确定要删除此唐卡？')) return
  try {
    await axios.delete(`${API}/api/v1/admin/gallery/${id}`, {
      headers: { 'X-Admin-Password': adminPassword.value }
    })
    await loadGallery()
  } catch (e) {
    console.error('删除失败', e)
  }
}

// `getVariants` has been removed as we now use backend-provided variant flags.
</script>

<style scoped>
/* --- Admin Layout --- */
.admin-panel {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0612 0%, #0d1b2a 100%);
  color: #e8dbb0;
  font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif;
  padding: 0 0 60px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(10, 6, 18, 0.9);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(201, 162, 39, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left { display: flex; gap: 16px; align-items: center; }
.admin-title { font-size: 20px; margin: 0; font-weight: 600; }
.admin-badge {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(201, 162, 39, 0.15);
  border: 1px solid rgba(201, 162, 39, 0.3);
  color: #c9a227;
}
.back-link {
  color: rgba(232, 219, 176, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}
.back-link:hover { color: #c9a227; }

/* --- Sections --- */
.admin-section {
  max-width: 1200px;
  margin: 32px auto;
  padding: 0 32px;
}

/* --- Health Dashboard --- */
.health-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 32px;
}

.health-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.health-icon {
  font-size: 28px;
  background: rgba(255, 255, 255, 0.05);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.health-info {
  flex: 1;
}

.health-label {
  font-size: 11px;
  color: rgba(232, 219, 176, 0.5);
  margin-bottom: 6px;
}

.health-value {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}
.health-value.ok { color: #4ecdc4; }
.health-value.pending { color: rgba(232, 219, 176, 0.4); font-weight: normal; }

.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #4ecdc4;
  transition: width 0.3s ease;
}
.progress-fill.warning {
  background: #c9a227;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.batch-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.batch-btn.ok:hover { background: rgba(78, 205, 196, 0.2); border-color: #4ecdc4; color: #4ecdc4; }
.batch-btn.dim:hover { background: rgba(255, 107, 107, 0.2); border-color: #ff6b6b; color: #ff6b6b; }
.batch-btn:disabled { opacity: 0.5; cursor: wait; }

.upload-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.upload-btn:hover { background: rgba(78, 205, 196, 0.3); }
.upload-btn:disabled { opacity: 0.5; cursor: wait; }

.count-badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
  background: rgba(201, 162, 39, 0.15);
  color: #c9a227;
}

/* --- Mode Toggle --- */
.mode-toggle-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.mode-label { font-size: 12px; color: rgba(232, 219, 176, 0.5); margin-bottom: 4px; }
.mode-value { font-size: 22px; font-weight: 700; }
.mode-value.preset { color: #c9a227; }
.mode-value.real { color: #4ecdc4; }
.mode-desc { font-size: 13px; color: rgba(232, 219, 176, 0.5); margin: 8px 0 0; max-width: 500px; }

.mode-switch-btn {
  padding: 10px 24px;
  border-radius: 8px;
  border: 1px solid rgba(201, 162, 39, 0.4);
  background: rgba(201, 162, 39, 0.1);
  color: #c9a227;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.mode-switch-btn:hover { background: rgba(201, 162, 39, 0.2); }
.mode-switch-btn:disabled { opacity: 0.5; cursor: wait; }

/* --- Gallery Grid --- */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.gallery-admin-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  transition: border-color 0.2s;
}
.gallery-admin-card:hover { border-color: rgba(201, 162, 39, 0.3); }

.card-preview {
  position: relative;
  height: 180px;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card-id {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 4px;
  font-size: 11px;
  color: #c9a227;
}

.card-info { padding: 12px; }
.card-title-input, .card-desc-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #e8dbb0;
  padding: 6px 0;
  font-size: 14px;
  outline: none;
  margin-bottom: 4px;
}
.card-title-input { font-weight: 600; }
.card-desc-input { font-size: 12px; color: rgba(232, 219, 176, 0.6); }
.card-title-input:focus, .card-desc-input:focus { border-bottom-color: #c9a227; }
.card-filename { font-size: 11px; color: rgba(232, 219, 176, 0.3); margin-top: 6px; }

.card-variants {
  padding: 8px 12px;
  display: flex;
  gap: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.variant-row { display: flex; gap: 4px; align-items: center; font-size: 11px; }
.variant-label { color: rgba(232, 219, 176, 0.5); }
.variant-status.ok { color: #4ecdc4; }
.variant-status.missing { color: #ff6b6b; font-weight: bold; }

.variant-warning {
  background: rgba(255, 107, 107, 0.15);
  color: #ff6b6b;
  font-size: 11px;
  text-align: center;
  padding: 4px 0;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 50, 50, 0.2);
  color: #ff6b6b;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}
.gallery-admin-card:hover .delete-btn { opacity: 1; }
.delete-btn:hover { background: rgba(255, 50, 50, 0.4); }

/* --- Login Screen --- */
.admin-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0612 0%, #0d1b2a 100%);
}

.login-card {
  text-align: center;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  max-width: 360px;
  width: 100%;
}

.login-icon { font-size: 48px; margin-bottom: 16px; }
.login-title { font-size: 22px; color: #e8dbb0; margin: 0 0 8px; }
.login-desc { font-size: 13px; color: rgba(232, 219, 176, 0.5); margin: 0 0 24px; }

.login-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e8dbb0;
  font-size: 15px;
  outline: none;
  margin-bottom: 16px;
  box-sizing: border-box;
}
.login-input:focus { border-color: #c9a227; }

.login-btn {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #c9a227, #a67f1a);
  color: #0a0612;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.login-btn:hover { opacity: 0.9; }
.login-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.login-error {
  color: #ff6b6b;
  font-size: 13px;
  margin: 12px 0 0;
}
</style>
