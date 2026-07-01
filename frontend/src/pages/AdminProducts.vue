<template>
  <div class="admin-products">
    <div class="header">
      <h2>商品管理</h2>
      <button class="add-btn" @click="showForm = true; editItem = null">+ 添加商品</button>
    </div>

    <div class="filter-bar">
      <select v-model="filterCat" @change="load">
        <option value="">全部分类</option>
        <option value="agent">Agent</option>
        <option value="dev_tool">开发工具</option>
        <option value="env_pack">环境包</option>
      </select>
    </div>

    <table class="product-table">
      <thead>
        <tr>
          <th>名称</th>
          <th>分类</th>
          <th>价格</th>
          <th>版本</th>
          <th>大小</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in products" :key="p.id">
          <td>{{ p.name }}</td>
          <td>{{ catLabels[p.category] || p.category }}</td>
          <td>¥{{ p.price_yuan }}</td>
          <td>{{ p.version || '-' }}</td>
          <td>{{ fmtSize(p.file_size) || '-' }}</td>
          <td><span :class="p.status === 'active' ? 'tag-on' : 'tag-off'">{{ p.status }}</span></td>
          <td class="actions">
            <button @click="editItem = { ...p }; showForm = true">编辑</button>
            <button class="danger" @click="del(p.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editItem?.id ? '编辑商品' : '添加商品' }}</h3>
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.name" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description" rows="3"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>分类</label>
            <select v-model="form.category">
              <option value="agent">Agent</option>
              <option value="dev_tool">开发工具</option>
              <option value="env_pack">环境包</option>
            </select>
          </div>
          <div class="form-group">
            <label>价格 (元)</label>
            <input type="number" v-model="form.price" step="0.01" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>版本</label>
            <input v-model="form.version" />
          </div>
          <div class="form-group">
            <label>系统要求</label>
            <input v-model="form.system_requirements" />
          </div>
        </div>
        <div class="form-group">
          <label>商品文件</label>
          <div class="file-section">
            <div v-if="editItem?.file_path" class="file-info">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M4 4h12v12H4z" stroke="currentColor" stroke-width="1.3" fill="none"/><path d="M10 6v6m-3-3l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="file-name">{{ fileName }}</span>
              <span class="file-size">{{ fmtSize(editItem.file_size) }}</span>
              <button class="file-del-btn" @click="deleteFile" :disabled="uploading">删除</button>
            </div>
            <div class="file-upload-row">
              <input ref="fileInput" type="file" class="file-input-hidden" @change="onFileChange" />
              <button class="upload-btn" @click="$refs.fileInput.click()" :disabled="uploading || !editItem?.id">
                {{ editItem?.file_path ? '更换文件' : '选择文件' }}
              </button>
              <span v-if="selectedFile" class="selected-name">{{ selectedFile.name }} ({{ fmtSize(selectedFile.size) }})</span>
              <button v-if="selectedFile && !uploading" class="confirm-upload-btn" @click="uploadFile">上传</button>
            </div>
            <div v-if="uploading" class="upload-progress">
              <div class="progress-bar"><div class="progress-fill" :style="{ width: uploadProgress + '%' }" /></div>
              <span class="progress-text">上传中... {{ uploadProgress }}%</span>
            </div>
            <div v-if="uploadMsg" :class="['upload-msg', uploadMsgType]">{{ uploadMsg }}</div>
            <div v-if="!editItem?.id" class="file-hint">请先创建商品后再上传文件</div>
          </div>
        </div>
        <div class="form-actions">
          <button class="cancel-btn" @click="showForm = false">取消</button>
          <button class="save-btn" @click="save">{{ editItem?.id ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { api } from '../api'

const products = ref([])
const showForm = ref(false)
const filterCat = ref('')
const editItem = ref(null)

const catLabels = { agent: 'Agent', dev_tool: '开发工具', env_pack: '环境包' }

const form = reactive({
  name: '', description: '', category: 'agent', price: 0,
  version: '', system_requirements: '',
})

// File upload state
const fileInput = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMsg = ref('')
const uploadMsgType = ref('')

const fileName = computed(() => {
  if (!editItem.value?.file_path) return ''
  return editItem.value.file_path.split(/[/\\]/).pop()
})

function fmtSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function resetForm() {
  Object.assign(form, { name: '', description: '', category: 'agent', price: 0, version: '', system_requirements: '' })
  editItem.value = null
  selectedFile.value = null
  uploadMsg.value = ''
}

async function load() {
  try {
    const res = await api.adminListProducts(filterCat.value || undefined)
    products.value = res.items || []
  } catch (_) { products.value = [] }
}

async function save() {
  try {
    let result
    if (editItem.value?.id) {
      result = await api.adminUpdateProduct(editItem.value.id, form)
    } else {
      result = await api.adminCreateProduct({ ...form })
    }
    if (!editItem.value?.id) editItem.value = result
    showForm.value = false
    resetForm()
    load()
  } catch (e) { alert('操作失败: ' + e.message) }
}

async function del(id) {
  if (!confirm('确定删除该商品？')) return
  try { await api.adminDeleteProduct(id); load() }
  catch (e) { alert('删除失败: ' + e.message) }
}

function onFileChange(e) {
  selectedFile.value = e.target.files[0] || null
  uploadMsg.value = ''
}

async function uploadFile() {
  if (!selectedFile.value || !editItem.value?.id) return
  uploading.value = true
  uploadProgress.value = 0
  uploadMsg.value = ''
  try {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/admin/api/store/admin/products/${editItem.value.id}/upload`)
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        uploadProgress.value = Math.round((e.loaded / e.total) * 100)
      }
    }

    const result = await new Promise((resolve, reject) => {
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          try { reject(new Error(JSON.parse(xhr.responseText).error || 'upload_failed')) }
          catch { reject(new Error('upload_failed')) }
        }
      }
      xhr.onerror = () => reject(new Error('网络错误'))
      xhr.send(formData)
    })

    editItem.value.file_path = result.file_path
    editItem.value.file_size = result.file_size
    if (result.version) editItem.value.version = result.version
    selectedFile.value = null
    uploadMsg.value = '上传成功'
    uploadMsgType.value = 'success'
    load()
  } catch (e) {
    uploadMsg.value = '上传失败: ' + e.message
    uploadMsgType.value = 'error'
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function deleteFile() {
  if (!editItem.value?.id || !confirm('确定删除已上传的文件？')) return
  try {
    await api.adminDeleteProductFile(editItem.value.id)
    editItem.value.file_path = null
    editItem.value.file_size = null
    uploadMsg.value = '文件已删除'
    uploadMsgType.value = 'success'
    load()
  } catch (e) {
    uploadMsg.value = '删除失败: ' + e.message
    uploadMsgType.value = 'error'
  }
}

watch(showForm, (v) => { if (v) resetForm() })
load()
</script>

<style scoped>
.admin-products { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header h2 { margin: 0; }
.add-btn { padding: 8px 20px; border: none; border-radius: 8px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 500; }
.filter-bar { margin-bottom: 16px; }
.filter-bar select { padding: 6px 12px; border: 1px solid var(--border); border-radius: 6px; }
.product-table { width: 100%; border-collapse: collapse; }
.product-table th, .product-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border-light, #eee); font-size: 0.88rem; }
.product-table th { font-weight: 600; color: var(--text-muted); font-size: 0.8rem; }
.tag-on { padding: 2px 10px; border-radius: 8px; background: #d1fae5; color: #065f46; font-size: 0.78rem; }
.tag-off { padding: 2px 10px; border-radius: 8px; background: #fee2e2; color: #991b1b; font-size: 0.78rem; }
.actions { display: flex; gap: 6px; }
.actions button { padding: 4px 12px; border: 1px solid var(--border); border-radius: 6px; background: #fff; cursor: pointer; font-size: 0.8rem; }
.actions button.danger { color: #dc2626; border-color: #fca5a5; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 520px; max-width: 90vw; max-height: 85vh; overflow-y: auto; }
.modal h3 { margin: 0 0 20px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; color: var(--text-muted); margin-bottom: 4px; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.9rem; box-sizing: border-box; }
.form-row { display: flex; gap: 14px; }
.form-row .form-group { flex: 1; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.cancel-btn { padding: 8px 20px; border: 1px solid var(--border); border-radius: 8px; background: #fff; cursor: pointer; }
.save-btn { padding: 8px 20px; border: none; border-radius: 8px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 500; }

/* File upload styles */
.file-section { border: 1px dashed var(--border); border-radius: 8px; padding: 12px; background: #fafafa; }
.file-info { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; margin-bottom: 8px; color: #166534; font-size: 0.85rem; }
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.file-size { color: #6b7280; font-size: 0.8rem; }
.file-del-btn { padding: 2px 10px; border: 1px solid #fca5a5; border-radius: 4px; background: #fff; color: #dc2626; cursor: pointer; font-size: 0.78rem; }
.file-upload-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.file-input-hidden { display: none; }
.upload-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: #fff; cursor: pointer; font-size: 0.82rem; }
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.selected-name { font-size: 0.82rem; color: #374151; }
.confirm-upload-btn { padding: 6px 14px; border: none; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; font-size: 0.82rem; }
.upload-progress { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.progress-bar { flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #2563eb); border-radius: 3px; transition: width 0.2s; }
.progress-text { font-size: 0.78rem; color: #6b7280; white-space: nowrap; }
.upload-msg { margin-top: 6px; font-size: 0.8rem; padding: 4px 10px; border-radius: 4px; }
.upload-msg.success { color: #166534; background: #f0fdf4; }
.upload-msg.error { color: #991b1b; background: #fee2e2; }
.file-hint { margin-top: 6px; font-size: 0.78rem; color: #9ca3af; font-style: italic; }
</style>
