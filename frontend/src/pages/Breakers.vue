<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">{{ t('breakerMonitor') }}</n-h1>
      <n-button @click="refresh">{{ t('refresh') }}</n-button>
    </n-space>

    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="breakers" :bordered="false" :min-height="80" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NCard, NDataTable, NH1, NButton, NTag, NEmpty, NPopconfirm, NText } from 'naive-ui'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()

const breakers = ref([])

const tableColumns = [
  { title: '供应商', key: 'provider', render: (row) => h('strong', row.provider) },
  { title: t('status'), key: 'status', render: (row) => h(NTag, {
    type: row.status === 'closed' ? 'success' : row.status === 'open' ? 'error' : 'warning',
    size: 'small',
  }, { default: () => row.status }) },
  { title: '失败次数', key: 'failure_count' },
  { title: t('lastFailureTime'), key: 'last_failure_time',
    render: (row) => row.last_failure_time > 0
      ? new Date(row.last_failure_time * 1000).toLocaleString()
      : '-' },
  { title: t('operation'), key: 'actions',
    render: (row) => row.status !== 'closed'
      ? h(NButton, { size: 'small', color: '#dc2626', onClick: () => resetBreaker(row.provider) }, { default: () => t('reset') })
      : h(NText, { depth: 3 }, '-') },
]

async function loadBreakers() {
  try { breakers.value = await gatewayApi.listCircuitBreakers() } catch (e) { /* */ }
}
onMounted(loadBreakers)

async function resetBreaker(provider) {
  try { await gatewayApi.resetCircuitBreaker(provider); await loadBreakers() } catch (e) { /* */ }
}
async function refresh() { await loadBreakers() }
</script>
