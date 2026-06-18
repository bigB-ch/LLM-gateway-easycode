<template>
  <div>
    <n-h1 style="margin-bottom:24px">{{ t('adminUserDaily') }}</n-h1>

    <!-- Filter bar -->
    <n-card :bordered="true" size="small" style="margin-bottom:16px">
      <n-space align="center" :size="8" wrap>
        <n-text style="font-size:12px">{{ t('date') }}：</n-text>
        <n-date-picker v-model:value="dateFromTs" type="date" placeholder="开始日期" style="width:auto" />
        <n-text depth="3">~</n-text>
        <n-date-picker v-model:value="dateToTs" type="date" placeholder="结束日期" style="width:auto" />
        <n-button size="small" type="primary" @click="search">{{ t('query') }}</n-button>
        <n-button size="small" @click="resetFilter">{{ t('reset') }}</n-button>
      </n-space>
    </n-card>

    <!-- Data table -->
    <n-card :bordered="true">
      <n-data-table
        :columns="tableColumns"
        :data="items"
        :bordered="false"
        :single-line="false"
        :min-height="100"
      />
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
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard, NDataTable, NDatePicker, NH1, NPagination, NButton,
  NSpace, NTag, NText,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()

const items = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const dateFromTs = ref(null)
const dateToTs = ref(null)

const dateFrom = computed(() => dateFromTs.value ? new Date(dateFromTs.value).toISOString().slice(0, 10) : undefined)
const dateTo = computed(() => dateToTs.value ? new Date(dateToTs.value).toISOString().slice(0, 10) : undefined)

const tableColumns = [
  { title: t('date'), key: 'date', width: 110, render: (row) => h('span', { style: 'font-weight:500' }, row.date) },
  { title: t('user'), key: 'username', render: (row) => h('span', { style: 'font-weight:600;font-size:13px' }, row.username) },
  { title: t('email'), key: 'email', render: (row) => h('span', { style: 'color:var(--text-muted);font-size:11px' }, row.email) },
  { title: t('model'), key: 'model', width: 150,
    render: (row) => h('span', {
      style: 'font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block',
      title: row.model,
    }, row.model) },
  { title: t('calls'), key: 'calls', width: 80,
    render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.calls || 0).toLocaleString()) },
  { title: t('success'), key: 'success', width: 70,
    render: (row) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.success || 0 }) },
  { title: t('inputToken'), key: 'prompt_tokens',
    render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.prompt_tokens || 0).toLocaleString()) },
  { title: t('outputToken'), key: 'completion_tokens',
    render: (row) => h('span', { style: 'font-family:monospace;font-size:12px' }, (row.completion_tokens || 0).toLocaleString()) },
  { title: t('cost'), key: 'cost_yuan', width: 100,
    render: (row) => h('span', { style: 'font-family:monospace;font-size:12px;color:var(--primary)' }, '¥' + (row.cost_yuan || '0.00')) },
]

async function loadData() {
  try {
    const res = await api.getUserDaily(page.value, 20, dateFrom.value, dateTo.value)
    items.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
}

function goPage(p) {
  page.value = p
  loadData()
}

function search() {
  page.value = 1
  loadData()
}

function resetFilter() {
  dateFromTs.value = null
  dateToTs.value = null
  page.value = 1
  loadData()
}

onMounted(loadData)
</script>
