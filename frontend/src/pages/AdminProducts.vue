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
          <label>文件路径（服务器路径）</label>
          <input v-model="form.file_path" />
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
import { ref, reactive, watch } from 'vue'
import { api } from '../api'

const products = ref([])
const showForm = ref(false)
const filterCat = ref('')
const editItem = ref(null)

const catLabels = { agent: 'Agent', dev_tool: '开发工具', env_pack: '环境包' }

const form = reactive({
  name: '', description: '', category: 'agent', price: 0,
  version: '', system_requirements: '', file_path: '',
})

function resetForm() {
  Object.assign(form, { name: '', description: '', category: 'agent', price: 0, version: '', system_requirements: '', file_path: '' })
  editItem.value = null
}

async function load() {
  try {
    const res = await api.adminListProducts(filterCat.value || undefined)
    products.value = res.items || []
  } catch (_) { products.value = [] }
}

async function save() {
  try {
    if (editItem.value?.id) {
      await api.adminUpdateProduct(editItem.value.id, form)
    } else {
      await api.adminCreateProduct({ ...form })
    }
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
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 480px; max-width: 90vw; max-height: 85vh; overflow-y: auto; }
.modal h3 { margin: 0 0 20px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; color: var(--text-muted); margin-bottom: 4px; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.9rem; box-sizing: border-box; }
.form-row { display: flex; gap: 14px; }
.form-row .form-group { flex: 1; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.cancel-btn { padding: 8px 20px; border: 1px solid var(--border); border-radius: 8px; background: #fff; cursor: pointer; }
.save-btn { padding: 8px 20px; border: none; border-radius: 8px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 500; }
</style>
