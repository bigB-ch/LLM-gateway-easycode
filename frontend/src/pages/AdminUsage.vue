<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">{{ t('globalUsageLog') }}</n-h1>
      <n-button size="small" @click="loadUsage">{{ t('refresh') }}</n-button>
    </n-space>

    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="logs" :bordered="false" :single-line="false" :min-height="100" />
      <template v-if="totalPages > 1" #footer>
        <n-space align="center" justify="space-between">
          <n-text depth="3" style="font-size:12px">{{ t('totalRecords', { n: total }) }}</n-text>
          <n-pagination :page="page" :page-count="totalPages" :page-slot="5" @update:page="goPage" />
        </n-space>
      </template>
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NCard, NDataTable, NH1, NPagination, NButton, NSpace, NTag, NText } from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const logs = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)

const tableColumns = [
  { title: t('time'), key: 'created_at', render: (row) => h('span', { style: 'font-size:11px;white-space:nowrap' }, formatTime(row.created_at)) },
  { title: t('model'), key: 'model', render: (row) => h('span', { style: 'font-weight:500;font-size:13px' }, row.model) },
  { title: t('supplier'), key: 'provider', render: (row) => h('span', { style: 'font-size:12px' }, row.provider) },
  { title: t('inputToken'), key: 'prompt_tokens', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.prompt_tokens || 0).toLocaleString()) },
  { title: t('outputToken'), key: 'completion_tokens', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.completion_tokens || 0).toLocaleString()) },
  { title: t('cost'), key: 'cost_yuan', render: (row) => h('span', { style: 'font-family:monospace;font-size:12px;color:var(--primary)' }, '¥' + row.cost_yuan) },
  { title: t('duration'), key: 'latency_ms', render: (row) => row.latency_ms + 'ms' },
  { title: t('status'), key: 'status', render: (row) => h(NTag, { type: row.status === 'success' ? 'success' : 'error', size: 'tiny' }, { default: () => row.status === 'success' ? t('success') : t('error') }) },
]

async function loadUsage() {
  try {
    const res = await api.getAllUsage(page.value, 20)
    logs.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
}
onMounted(loadUsage)

function goPage(p) { page.value = p; loadUsage() }
function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
