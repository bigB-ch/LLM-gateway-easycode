<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">公告管理</n-h1>
      <n-button type="primary" @click="showAdd = true" v-if="!showAdd">+ 添加公告</n-button>
    </n-space>

    <!-- Add form -->
    <n-card v-if="showAdd" :bordered="true" size="small" style="margin-bottom:24px">
      <n-space align="flex-end" :size="12">
        <n-form-item label="公告内容" style="flex:1">
          <n-input v-model:value="newContent" placeholder="输入公告内容..." @keyup.enter="addAnnouncement" />
        </n-form-item>
        <n-button type="primary" :loading="adding" @click="addAnnouncement">{{ adding ? '添加中...' : '添加' }}</n-button>
        <n-button @click="showAdd = false; newContent = ''">取消</n-button>
      </n-space>
    </n-card>

    <!-- Edit row -->
    <n-card v-if="editingId" :bordered="true" size="small" style="margin-bottom:24px">
      <n-space align="flex-end" :size="12">
        <n-form-item label="编辑公告" style="flex:1">
          <n-input v-model:value="editContent" @keyup.enter="saveEdit" />
        </n-form-item>
        <n-button type="primary" :loading="saving" @click="saveEdit">保存</n-button>
        <n-button @click="editingId = ''; editContent = ''">取消</n-button>
      </n-space>
    </n-card>

    <!-- List -->
    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="items" :bordered="false" :min-height="80" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { NCard, NDataTable, NH1, NButton, NInput, NSpace, NFormItem, NPopconfirm } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const dialog = useDialog()

const items = ref([])
const showAdd = ref(false)
const newContent = ref('')
const adding = ref(false)
const editingId = ref('')
const editContent = ref('')
const saving = ref(false)

const tableColumns = [
  { title: '内容', key: 'content' },
  { title: '时间', key: 'date' },
  {
    title: '操作', key: 'actions', width: 120,
    render: (row) => h('div', { style: 'display:flex;gap:4px' }, [
      h(NButton, { size: 'small', onClick: () => startEdit(row) }, { default: () => '编辑' }),
      h(NPopconfirm, {
        onPositiveClick: () => removeAnnouncement(row.id),
      }, {
        trigger: () => h(NButton, { size: 'small', color: '#dc2626' }, { default: () => '删除' }),
        default: () => '确定删除？',
      }),
    ]),
  },
]

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
    message.success('添加成功')
  } catch (e) { message.error('添加失败: ' + e.message) }
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
    message.success('保存成功')
  } catch (e) { message.error('保存失败: ' + e.message) }
  finally { saving.value = false }
}

async function removeAnnouncement(id) {
  try { await api.deleteAnnouncement(id); await loadItems(); message.success('已删除') }
  catch (e) { message.error('删除失败: ' + e.message) }
}
</script>
