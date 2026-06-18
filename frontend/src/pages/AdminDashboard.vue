<template>
  <div>
    <n-h1 style="margin-bottom:24px">{{ t('platformOverview') }}</n-h1>

    <!-- Stat cards -->
    <n-grid :x-gap="16" :y-gap="16" :cols="4" style="margin-bottom:16px">
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('totalUsers')" :value="stats.total_users" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('todayCalls')" :value="(stats.today_calls || 0).toLocaleString()" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('todayRevenue')" :value="'¥' + (stats.today_revenue_yuan || '0')" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('activeSuppliers')" :value="stats.active_suppliers" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- Trend Chart -->
    <n-card :bordered="true" style="margin-bottom:16px">
      <n-h3 style="margin:0 0 16px">消耗趋势（近7天）</n-h3>
      <div v-if="trendData.length" style="position:relative;height:170px">
        <svg width="600" height="170" style="width:100%">
          <polygon :points="chartArea" fill="rgba(99,102,241,0.1)" />
          <polyline :points="chartPoints" fill="none" stroke="var(--primary)" stroke-width="2" />
          <circle v-for="(d, i) in trendData" :key="i" :cx="x(i)" :cy="y(d.cost_yuan)" r="3" fill="var(--primary)" />
          <text v-for="(d, i) in trendData" :key="'l'+i" :x="x(i)" y="160" text-anchor="end" transform="rotate(-45,x(i),160)" style="font-size:10px;fill:var(--text-muted)">{{ d.date.slice(5) }}</text>
        </svg>
      </div>
      <n-empty v-else description="暂无数据" style="padding:32px 0" />
    </n-card>

    <!-- Daily Summary Table -->
    <n-card :bordered="true" style="margin-bottom:16px">
      <template #header>
        <n-space align="center" justify="space-between">
          <n-h3 style="margin:0">每日消耗明细</n-h3>
        </n-space>
      </template>
      <n-data-table
        :columns="dailyColumns"
        :data="dailyItems"
        :bordered="false"
        :single-line="false"
        :min-height="100"
      />
      <template v-if="totalPages > 1" #footer>
        <n-space align="center" justify="space-between">
          <n-text depth="3" style="font-size:12px">共 {{ dailyTotal }} 天</n-text>
          <n-pagination :page="dailyPage" :page-count="totalPages" :page-slot="5" @update:page="goDaily" />
        </n-space>
      </template>
    </n-card>

    <!-- Two-column detail -->
    <n-grid :x-gap="16" :cols="2">
      <n-grid-item>
        <n-card :bordered="true">
          <n-h3 style="margin:0 0 16px">{{ t('todayTopModels') }}</n-h3>
          <div v-if="stats.top_models && stats.top_models.length > 0">
            <div v-for="(m, i) in stats.top_models" :key="m.model" class="flex-between" style="padding:8px 0;border-bottom:1px solid var(--border-light)">
              <n-space :size="8" align="center">
                <n-text depth="3" style="font-weight:700;font-size:14px">{{ i + 1 }}</n-text>
                <n-text style="font-weight:500">{{ m.model }}</n-text>
              </n-space>
              <n-text style="font-weight:600;font-size:13px">{{ m.count }} 次</n-text>
            </div>
          </div>
          <n-empty v-else :description="t('breakersNoData')" style="padding:20px" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card :bordered="true">
          <n-h3 style="margin:0 0 16px">{{ t('recentCalls') }}</n-h3>
          <div v-if="stats.recent_calls && stats.recent_calls.length > 0">
            <div v-for="log in stats.recent_calls.slice(0, 8)" :key="log.id" class="flex-between" style="padding:6px 0;border-bottom:1px solid var(--border-light);font-size:12px">
              <div style="flex:1;min-width:0">
                <n-text style="font-weight:500">{{ log.model }}</n-text>
                <n-text depth="3" style="margin-left:4px">{{ log.provider }}</n-text>
              </div>
              <n-space :size="12" align="center" style="flex-shrink:0">
                <n-tag :type="log.status === 'success' ? 'success' : 'error'" size="tiny">{{ log.status === 'success' ? '成功' : '失败' }}</n-tag>
                <n-text style="font-family:monospace">¥{{ log.cost_yuan }}</n-text>
                <n-text depth="3">{{ log.latency_ms }}ms</n-text>
              </n-space>
            </div>
          </div>
          <n-empty v-else :description="t('noData')" style="padding:20px" />
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard, NDataTable, NEmpty, NGrid, NGridItem, NH1, NH3,
  NPagination, NSpace, NStatistic, NTag, NText,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()

const stats = ref({ total_users: '-', today_calls: '-', today_revenue_yuan: '-', active_suppliers: '-', top_models: [], recent_calls: [] })
const trendData = ref([])
const dailyItems = ref([])
const dailyPage = ref(1)
const dailyTotal = ref(0)
const totalPages = ref(1)

const dailyColumns = [
  { title: '日期', key: 'date', width: 120, render: (row) => h('span', { style: 'font-weight:500' }, row.date) },
  { title: '总调用', key: 'calls', width: 80 },
  { title: '成功', key: 'success', width: 80, render: (row) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.success }) },
  { title: '输入 Token', key: 'prompt_tokens', render: (row) => (row.prompt_tokens || 0).toLocaleString() },
  { title: '输出 Token', key: 'completion_tokens', render: (row) => (row.completion_tokens || 0).toLocaleString() },
  { title: '消耗(元)', key: 'cost_yuan', render: (row) => h('span', { style: 'font-weight:600;color:var(--primary)' }, '¥' + row.cost_yuan) },
]

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))

function x(i) { return 40 + (i / Math.max(trendData.value.length - 1, 1)) * (600 - 80) }
function y(v) { return 150 - (v / maxCost.value) * 130 }
const chartPoints = computed(() => trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' '))
const chartArea = computed(() => `${x(0)},150 ` + trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' ') + ` ${x(Math.max(trendData.value.length - 1, 0))},150`)

onMounted(async () => {
  try { stats.value = await api.getAdminDashboard() } catch (e) { /* */ }
  try { const tr = await api.getAdminTrend(7); trendData.value = tr.trend || [] } catch (e) { /* */ }
  await loadDaily()
})

async function loadDaily() {
  try {
    const d = await api.getAdminDaily(dailyPage.value, 14)
    dailyItems.value = d.items || []
    dailyTotal.value = d.total || 0
    totalPages.value = Math.ceil(dailyTotal.value / 14) || 1
  } catch (e) { /* */ }
}
function goDaily(p) { dailyPage.value = p; loadDaily() }
</script>
