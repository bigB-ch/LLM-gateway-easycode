<template>
  <div>
    <!-- Stat tags -->
    <n-space :size="12" style="margin-bottom:16px">
      <n-card :bordered="true" size="small" style="padding:4px 16px">
        <n-text depth="3" style="font-size:11px">消耗额度</n-text>
        <n-text style="font-size:20px;font-weight:700;display:block;color:var(--primary)">&yen;{{ totalCost }}</n-text>
      </n-card>
      <n-card :bordered="true" size="small" style="padding:4px 16px">
        <n-text depth="3" style="font-size:11px;color:var(--danger)">RPM</n-text>
        <n-text style="font-size:20px;font-weight:700;display:block">{{ rpm }}</n-text>
      </n-card>
      <n-card :bordered="true" size="small" style="padding:4px 16px">
        <n-text depth="3" style="font-size:11px">TPM</n-text>
        <n-text style="font-size:20px;font-weight:700;display:block">{{ tpm }}</n-text>
      </n-card>
    </n-space>

    <!-- Filter bar -->
    <n-card :bordered="true" size="small" style="margin-bottom:16px">
      <n-space align="flex-end" wrap :size="[10, 6]">
        <n-form-item :label="t('dateRange')" style="font-size:11px">
          <n-date-picker v-model:value="dateFromTs" type="date" placeholder="开始" style="width:130px" />
        </n-form-item>
        <n-text depth="3">~</n-text>
        <n-form-item label-width="0" style="font-size:11px">
          <n-date-picker v-model:value="dateToTs" type="date" placeholder="结束" style="width:130px" />
        </n-form-item>
        <n-form-item :label="t('filterKeyName')" style="font-size:11px">
          <n-input v-model:value="filterKeyName" placeholder="搜索" size="small" style="width:110px" />
        </n-form-item>
        <n-form-item :label="t('filterModel')" style="font-size:11px">
          <n-input v-model:value="filterModel" placeholder="搜索" size="small" style="width:110px" />
        </n-form-item>
        <n-form-item :label="t('filterGroup')" style="font-size:11px">
          <n-input v-model:value="filterGroup" placeholder="搜索" size="small" style="width:90px" />
        </n-form-item>
        <n-form-item :label="t('filterReqId')" style="font-size:11px">
          <n-input v-model:value="filterReqId" placeholder="搜索" size="small" style="width:140px" />
        </n-form-item>
        <n-form-item :label="t('filterStatus')" style="font-size:11px">
          <n-select v-model:value="filterStatus" :options="[{label:t('all'),value:''},{label:t('success'),value:'success'},{label:t('error'),value:'error'}]" size="small" style="width:80px" />
        </n-form-item>
        <n-space :size="6" style="align-self:flex-end">
          <n-button size="small" type="primary" @click="doSearch">{{ t('query') }}</n-button>
          <n-button size="small" @click="resetFilter">{{ t('reset') }}</n-button>
          <n-button size="small">{{ t('columnSettings') }}</n-button>
        </n-space>
      </n-space>
    </n-card>

    <!-- Table -->
    <n-card :bordered="true">
      <n-data-table v-if="filteredLogs.length" :columns="tableColumns" :data="filteredLogs" :bordered="false" :single-line="false" :min-height="100" />
      <n-empty v-else :description="hasFilter ? t('adjustFilterHint') : t('noUsageData')" style="padding:40px 0" />
      <template #footer>
        <n-space justify="center" :size="8">
          <n-button size="small" :disabled="page <= 1" @click="loadPage(1)">{{ t('prevPage') }}</n-button>
          <n-button size="small" @click="loadPage(page + 1)">{{ t('nextPage') }}</n-button>
        </n-space>
      </template>
    </n-card>

    <!-- Detail modal -->
    <n-modal v-model:show="showDetail" preset="card" title="调用详情" style="max-width:480px" :bordered="true">
      <n-space vertical :size="8">
        <n-text depth="2" style="font-size:12px">Request ID: <n-code>{{ detailLog?.id }}</n-code></n-text>
        <n-text depth="2" style="font-size:12px">模型: {{ detailLog?.model }}</n-text>
        <n-text depth="2" style="font-size:12px">时间: {{ fmtTime(detailLog?.created_at) }}</n-text>
        <n-text depth="2" style="font-size:12px">耗时: {{ detailLog?.duration_ms || '-' }}ms</n-text>
        <n-text depth="2" style="font-size:12px">Tokens: {{ detailLog?.prompt_tokens }} in / {{ detailLog?.completion_tokens }} out</n-text>
        <n-text depth="2" style="font-size:12px">花费: &yen;{{ detailLog?.cost_yuan || '0.00' }}</n-text>
        <n-text depth="2" style="font-size:12px">IP: {{ detailLog?.ip || '-' }}</n-text>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard, NCode, NDataTable, NDatePicker, NEmpty, NButton,
  NFormItem, NInput, NModal, NSelect, NSpace, NText, NTag,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const logs = ref([])
const page = ref(1)
const detailLog = ref(null)
const showDetail = ref(false)

const dateFromTs = ref(null)
const dateToTs = ref(null)
const filterKeyName = ref('')
const filterModel = ref('')
const filterGroup = ref('')
const filterReqId = ref('')
const filterStatus = ref('')

const totalCost = ref('0.00')
const rpm = ref(0)
const tpm = ref(0)

const hasFilter = computed(() =>
  dateFromTs.value || dateToTs.value || filterKeyName.value || filterModel.value ||
  filterGroup.value || filterReqId.value || filterStatus.value
)

const filteredLogs = computed(() => {
  let list = logs.value
  if (filterKeyName.value) list = list.filter(l => (l.key_name || '').includes(filterKeyName.value))
  if (filterModel.value) list = list.filter(l => l.model.includes(filterModel.value))
  if (filterGroup.value) list = list.filter(l => (l.group || '').includes(filterGroup.value))
  if (filterReqId.value) list = list.filter(l => l.id.includes(filterReqId.value))
  if (filterStatus.value) list = list.filter(l => l.status === filterStatus.value)
  return list
})

const tableColumns = [
  { title: t('time'), key: 'created_at', render: (row) => h('span', { style: 'font-size:12px;white-space:nowrap' }, fmtTime(row.created_at)) },
  { title: t('token'), key: 'key_name', render: (row) => h('span', { style: 'font-size:12px' }, row.key_name || '默认') },
  { title: t('groups'), key: 'group', render: () => '-' },
  { title: t('type'), key: 'type', render: () => h(NTag, { size: 'tiny', type: 'primary' }, { default: () => 'chat' }) },
  { title: t('model'), key: 'model', render: (row) => h('code', { style: 'font-size:11px' }, row.model) },
  { title: t('duration'), key: 'latency_ms', render: (row) => (row.latency_ms || '-') + 'ms' },
  { title: t('input'), key: 'prompt_tokens' },
  { title: t('output'), key: 'completion_tokens' },
  { title: t('cost'), key: 'cost_yuan', render: (row) => '¥' + (row.cost_yuan || '0.00') },
  { title: 'IP', key: 'ip', render: (row) => row.ip || '-' },
  {
    title: t('details'), key: 'actions', width: 60,
    render: (row) => h(NButton, { size: 'tiny', onClick: () => { detailLog.value = row; showDetail.value = true } }, { default: () => '详情' }),
  },
]

onMounted(() => loadPage(1))

async function loadPage(p) {
  page.value = p
  try {
    const dateFrom = dateFromTs.value ? new Date(dateFromTs.value).toISOString().slice(0, 10) : null
    const dateTo = dateToTs.value ? new Date(dateToTs.value).toISOString().slice(0, 10) : null
    const data = await api.getUsage(p, dateFrom, dateTo)
    logs.value = data.items || []
    totalCost.value = data.total_cost_yuan || '0.00'
    rpm.value = '-'
    tpm.value = '-'
  } catch (e) { /* */ }
}

function doSearch() { loadPage(1) }
function resetFilter() {
  dateFromTs.value = null; dateToTs.value = null; filterKeyName.value = ''
  filterModel.value = ''; filterGroup.value = ''; filterReqId.value = ''
  filterStatus.value = ''
  loadPage(1)
}

function fmtTime(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN')
}
</script>
