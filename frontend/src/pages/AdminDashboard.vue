<template>
  <div>
    <h1 class="page-title mb-24">{{ t('platformOverview') }}</h1>

    <div class="stat-grid">
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F465;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">{{ t('totalUsers') }}</div>
        </div>
      </div>
      <div class="stat-card mc-purple">
        <div class="stat-icon">&#x26A1;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.today_calls }}</div>
          <div class="stat-label">{{ t('todayCalls') }}</div>
        </div>
      </div>
      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x1F4B0;</div>
        <div class="stat-body">
          <div class="stat-value">&yen;{{ stats.today_revenue_yuan }}</div>
          <div class="stat-label">{{ t('todayRevenue') }}</div>
        </div>
      </div>
      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x2699;&#xFE0F;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.active_suppliers }}</div>
          <div class="stat-label">{{ t('activeSuppliers') }}</div>
        </div>
      </div>
    </div>

    <!-- Trend Chart -->
    <div class="card card-padded" style="margin-top:24px">
      <h3 class="section-title mb-16">消耗趋势（近7天）</h3>
      <div v-if="trendData.length" style="position:relative;height:170px">
        <svg width="600" height="170" style="width:100%">
          <polygon :points="chartArea" fill="rgba(99,102,241,0.1)" />
          <polyline :points="chartPoints" fill="none" stroke="var(--primary)" stroke-width="2" />
          <circle v-for="(d, i) in trendData" :key="i" :cx="x(i)" :cy="y(d.cost_yuan)" r="3" fill="var(--primary)" />
          <text v-for="(d, i) in trendData" :key="'l'+i" :x="x(i)" y="160" text-anchor="end" transform="rotate(-45,x(i),160)" style="font-size:10px;fill:var(--text-muted)">{{ d.date.slice(5) }}</text>
        </svg>
      </div>
      <div v-else class="empty-state" style="padding:32px">
        <div class="empty-state-text">暂无数据</div>
      </div>
    </div>

    <!-- Daily Summary Table -->
    <div class="card" style="margin-top:16px">
      <div class="card-padded flex-between">
        <h3 class="section-title">每日消耗明细</h3>
      </div>
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr><th>日期</th><th>总调用</th><th>成功</th><th>输入 Token</th><th>输出 Token</th><th>消耗(元)</th></tr>
          </thead>
          <tbody>
            <tr v-if="!dailyItems.length"><td colspan="6"><div class="empty-state" style="padding:40px"><div class="empty-state-text">暂无调用记录</div></div></td></tr>
            <tr v-for="d in dailyItems" :key="d.date">
              <td style="font-weight:500">{{ d.date }}</td>
              <td>{{ d.calls }}</td>
              <td><span class="badge badge-success" style="font-size:10px">{{ d.success }}</span></td>
              <td>{{ d.prompt_tokens?.toLocaleString() }}</td>
              <td>{{ d.completion_tokens?.toLocaleString() }}</td>
              <td style="font-weight:600;color:var(--primary)">&yen;{{ d.cost_yuan }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="totalPages > 1" class="card-padded flex-between">
        <span class="text-muted" style="font-size:12px">共 {{ dailyTotal }} 天</span>
        <div style="display:flex;gap:4px">
          <button class="btn btn-outline btn-xs" :disabled="dailyPage <= 1" @click="goDaily(dailyPage - 1)">上一页</button>
          <span class="text-muted" style="font-size:12px;padding:4px 8px">{{ dailyPage }} / {{ totalPages }}</span>
          <button class="btn btn-outline btn-xs" :disabled="dailyPage >= totalPages" @click="goDaily(dailyPage + 1)">下一页</button>
        </div>
      </div>
    </div>

    <!-- Two-column detail -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:24px">
      <div class="card card-padded">
        <h3 class="section-title mb-16">{{ t('todayTopModels') }}</h3>
        <div v-if="stats.top_models && stats.top_models.length > 0">
          <div v-for="(m, i) in stats.top_models" :key="m.model" class="flex-between" style="padding:8px 0;border-bottom:1px solid var(--border-light)">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-weight:700;font-size:14px;color:var(--text-secondary)">{{ i + 1 }}</span>
              <span style="font-weight:500">{{ m.model }}</span>
            </div>
            <span style="font-weight:600;font-size:13px">{{ m.count }} 次</span>
          </div>
        </div>
        <div v-else class="text-muted text-center" style="padding:20px">{{ t('breakersNoData') }}</div>
      </div>
      <div class="card card-padded">
        <h3 class="section-title mb-16">{{ t('recentCalls') }}</h3>
        <div v-if="stats.recent_calls && stats.recent_calls.length > 0">
          <div v-for="log in stats.recent_calls.slice(0, 8)" :key="log.id" class="flex-between" style="padding:6px 0;border-bottom:1px solid var(--border-light);font-size:12px">
            <div style="flex:1;min-width:0">
              <span style="font-weight:500">{{ log.model }}</span>
              <span class="text-muted" style="margin-left:4px">{{ log.provider }}</span>
            </div>
            <div style="display:flex;gap:12px;align-items:center;flex-shrink:0">
              <span :class="'badge ' + (log.status === 'success' ? 'badge-success' : 'badge-danger')" style="font-size:9px">{{ log.status === 'success' ? '成功' : '失败' }}</span>
              <span style="font-family:monospace">&yen;{{ log.cost_yuan }}</span>
              <span class="text-muted">{{ log.latency_ms }}ms</span>
            </div>
          </div>
        </div>
        <div v-else class="text-muted text-center" style="padding:20px">{{ t('noData') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const stats = ref({ total_users: '-', today_calls: '-', today_revenue_yuan: '-', active_suppliers: '-', top_models: [], recent_calls: [] })
const trendData = ref([])
const dailyItems = ref([])
const dailyPage = ref(1)
const dailyTotal = ref(0)
const totalPages = ref(1)

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))

function x(i) { return 40 + (i / Math.max(trendData.value.length - 1, 1)) * (600 - 80) }
function y(v) { return 150 - (v / maxCost.value) * 130 }
const chartPoints = computed(() => trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' '))
const chartArea = computed(() => `${x(0)},150 ` + trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' ') + ` ${x(Math.max(trendData.value.length - 1, 0))},150`)

onMounted(async () => {
  try { stats.value = await api.getAdminDashboard() } catch(e) {}
  try { const tr = await api.getAdminTrend(7); trendData.value = tr.trend || [] } catch(e) {}
  await loadDaily()
})

async function loadDaily() {
  try { const d = await api.getAdminDaily(dailyPage.value, 14); dailyItems.value = d.items || []; dailyTotal.value = d.total || 0; totalPages.value = Math.ceil(dailyTotal.value / 14) || 1 } catch(e) {}
}
function goDaily(p) { dailyPage.value = p; loadDaily() }
</script>
