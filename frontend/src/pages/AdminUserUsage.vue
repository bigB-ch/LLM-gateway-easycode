<template>
  <div>
    <n-h1 style="margin-bottom:24px">{{ t('adminUserUsage') }}</n-h1>

    <!-- All users usage summary table -->
    <n-card :bordered="true">
      <n-data-table
        :columns="tableColumns"
        :data="items"
        :bordered="false"
        :single-line="false"
        :loading="loading"
        :min-height="150"
      />
      <template v-if="totalPages > 1" #footer>
        <n-space align="center" justify="space-between">
          <n-text depth="3" style="font-size:12px">{{ t('totalRecords', { n: total }) }}</n-text>
          <n-pagination :page="page" :page-count="totalPages" :page-slot="5" @update:page="goPage" />
        </n-space>
      </template>
    </n-card>

    <!-- Per-model detail modal -->
    <n-modal v-model:show="showDetail" preset="card" :title="t('perModelUsage') + ' - ' + (detailUser?.username || '')"
      style="max-width:800px" :bordered="true">
      <div style="max-height:65vh;overflow-y:auto">
        <!-- Model summary -->
        <n-h4 style="margin:0 0 8px;font-size:13px;color:var(--text-muted)">{{ t('modelSummary') }}</n-h4>
        <n-data-table
          :columns="modelColumns"
          :data="detailModels"
          :bordered="false"
          :single-line="false"
          :min-height="60"
          style="margin-bottom:16px"
        />

        <!-- Detail logs -->
        <n-h4 style="margin:0 0 8px;font-size:13px;color:var(--text-muted)">{{ t('usageLogs') }}</n-h4>
        <n-data-table
          :columns="logColumns"
          :data="detailLogs"
          :bordered="false"
          :single-line="false"
          :min-height="60"
        />

        <!-- Pagination for detail logs -->
        <n-space v-if="detailTotalPages > 1" align="center" justify="space-between" style="padding:12px 0">
          <n-text depth="3" style="font-size:12px">{{ t('totalRecords', { n: detailTotal }) }}</n-text>
          <n-pagination :page="detailPage" :page-count="detailTotalPages" :page-slot="5" @update:page="detailGoPage" />
        </n-space>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import {
  NCard, NDataTable, NH1, NH4, NModal, NPagination, NSpace, NTag, NText, NButton,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()

const items = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const loading = ref(true)

// Detail modal
const showDetail = ref(false)
const detailUser = ref(null)
const detailModels = ref([])
const detailLogs = ref([])
const detailPage = ref(1)
const detailTotal = ref(0)
const detailTotalPages = ref(1)

const tableColumns = [
  { title: t('user'), key: 'username', render: (row) => h('span', { style: 'font-weight:500' }, row.username) },
  { title: t('email'), key: 'email', render: (row) => h('span', { style: 'color:var(--text-muted);font-size:12px' }, row.email) },
  { title: t('totalCalls'), key: 'calls', render: (row) => (row.calls || 0).toLocaleString() },
  { title: t('success'), key: 'success', render: (row) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.success }) },
  { title: t('inputToken'), key: 'prompt_tokens', render: (row) => (row.prompt_tokens || 0).toLocaleString() },
  { title: t('outputToken'), key: 'completion_tokens', render: (row) => (row.completion_tokens || 0).toLocaleString() },
  { title: t('totalCost'), key: 'cost_yuan', render: (row) => h('span', { style: 'font-family:monospace;color:var(--primary)' }, '¥' + row.cost_yuan) },
  { title: t('lastUsed'), key: 'last_used', render: (row) => h('span', { style: 'color:var(--text-muted);font-size:11px' }, formatTime(row.last_used)) },
  {
    title: t('operation'), key: 'actions', width: 80,
    render: (row) => h(NButton, { size: 'tiny', onClick: () => openDetail(row) }, { default: () => t('details') }),
  },
]

const modelColumns = [
  { title: t('model'), key: 'model', render: (row) => h('span', { style: 'font-weight:500' }, row.model) },
  { title: t('calls'), key: 'calls', render: (row) => (row.calls || 0).toLocaleString() },
  { title: t('success'), key: 'success', render: (row) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.success }) },
  { title: t('inputToken'), key: 'prompt_tokens', render: (row) => (row.prompt_tokens || 0).toLocaleString() },
  { title: t('outputToken'), key: 'completion_tokens', render: (row) => (row.completion_tokens || 0).toLocaleString() },
  { title: t('totalCost'), key: 'cost_yuan', render: (row) => h('span', { style: 'font-family:monospace;color:var(--primary)' }, '¥' + row.cost_yuan) },
]

const logColumns = [
  { title: t('time'), key: 'created_at', render: (row) => h('span', { style: 'font-size:11px;white-space:nowrap' }, formatTime(row.created_at)) },
  { title: t('model'), key: 'model', render: (row) => h('span', { style: 'font-weight:500;font-size:13px' }, row.model) },
  { title: t('supplier'), key: 'provider' },
  { title: t('inputToken'), key: 'prompt_tokens', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.prompt_tokens || 0).toLocaleString()) },
  { title: t('outputToken'), key: 'completion_tokens', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.completion_tokens || 0).toLocaleString()) },
  { title: t('cost'), key: 'cost_yuan', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px;color:var(--primary)' }, '¥' + row.cost_yuan) },
  { title: t('duration'), key: 'latency_ms', render: (row) => row.latency_ms + 'ms' },
  {
    title: t('status'), key: 'status', render: (row) => h(NTag, {
      type: row.status === 'success' ? 'success' : 'error',
      size: 'tiny',
    }, { default: () => row.status === 'success' ? t('success') : t('error') }),
  },
]

async function loadData() {
  loading.value = true
  try {
    const res = await api.getUserUsageSummary(page.value, 20)
    items.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
  loading.value = false
}

function goPage(p) {
  page.value = p
  loadData()
}

async function openDetail(row) {
  detailUser.value = row
  detailPage.value = 1
  showDetail.value = true
  await loadDetail()
}

async function loadDetail() {
  if (!detailUser.value) return
  try {
    const res = await api.getUserModelUsage(detailUser.value.user_id, detailPage.value, 20)
    detailModels.value = res.models || []
    detailLogs.value = res.logs || []
    detailTotal.value = res.total || 0
    detailTotalPages.value = Math.max(1, Math.ceil(detailTotal.value / 20))
  } catch (e) { /* */ }
}

function detailGoPage(p) {
  detailPage.value = p
  loadDetail()
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

onMounted(loadData)
</script>
