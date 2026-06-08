<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">公告管理</h1>
      <button class="btn btn-primary" @click="showAdd = true" v-if="!showAdd">+ 添加公告</button>
    </div>

    <!-- Add form -->
    <div v-if="showAdd" class="card card-padded mb-24">
      <div style="display:flex;gap:12px;align-items:flex-end">
        <div style="flex:1">
          <label class="form-label">公告内容</label>
          <input v-model="newContent" class="form-input" placeholder="输入公告内容..." @keyup.enter="addAnnouncement" />
        </div>
        <button class="btn btn-primary" @click="addAnnouncement" :disabled="adding">{{ adding ? '添加中...' : '添加' }}</button>
        <button class="btn btn-outline" @click="showAdd = false; newContent = ''">取消</button>
      </div>
    </div>

    <!-- Edit row -->
    <div v-if="editingId" class="card card-padded mb-24">
      <div style="display:flex;gap:12px;align-items:flex-end">
        <div style="flex:1">
          <label class="form-label">编辑公告</label>
          <input v-model="editContent" class="form-input" @keyup.enter="saveEdit" />
        </div>
        <button class="btn btn-primary" @click="saveEdit" :disabled="saving">保存</button>
        <button class="btn btn-outline" @click="editingId = ''; editContent = ''">取消</button>
      </div>
    </div>

    <!-- List -->
    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr><th>内容</th><th>时间</th><th style="width:120px">操作</th></tr>
          </thead>
          <tbody>
            <tr v-if="items.length === 0">
              <td colspan="3"><div class="empty-state"><div class="empty-state-text">暂无公告</div></div></td>
            </tr>
            <tr v-for="a in items" :key="a.id">
              <td>{{ a.content }}</td>
              <td class="text-secondary">{{ a.date }}</td>
              <td>
                <button class="btn btn-outline btn-sm" @click="startEdit(a)" style="margin-right:4px">编辑</button>
                <button class="btn btn-danger btn-sm" @click="removeAnnouncement(a.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const items = ref([])
const showAdd = ref(false)
const newContent = ref('')
const adding = ref(false)
const editingId = ref('')
const editContent = ref('')
const saving = ref(false)

onMounted(loadItems)

async function loadItems() {
  try { items.value = (await api.listAnnouncements()).items || [] } catch (e) { /* */ }
}

async function addAnnouncement() {
  if (!newContent.value.trim()) return
  adding.value = true
  try {
    await api.createAnnouncement(newContent.value.trim())
    newContent.value = ''
    showAdd.value = false
    await loadItems()
  } catch (e) { alert('添加失败: ' + e.message) }
  finally { adding.value = false }
}

function startEdit(a) {
  editingId.value = a.id
  editContent.value = a.content
}

async function saveEdit() {
  if (!editContent.value.trim()) return
  saving.value = true
  try {
    await api.updateAnnouncement(editingId.value, editContent.value.trim())
    editingId.value = ''
    editContent.value = ''
    await loadItems()
  } catch (e) { alert('保存失败: ' + e.message) }
  finally { saving.value = false }
}

async function removeAnnouncement(id) {
  if (!confirm('确定删除？')) return
  try { await api.deleteAnnouncement(id); await loadItems() } catch (e) { alert('删除失败: ' + e.message) }
}
</script>
