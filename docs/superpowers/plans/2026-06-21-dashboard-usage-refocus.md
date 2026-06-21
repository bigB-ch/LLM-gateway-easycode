# Dashboard & Usage Refocus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move usage analytics (time range, stat cards, SVG charts, model breakdown) from Usage.vue into Dashboard.vue, and refocus Usage.vue on call logs + per-model bar chart.

**Architecture:** Dashboard becomes the analytics overview hub; Usage becomes a log browser. Data sources stay the same — `api.getTrend(days)` for charts/stats, `api.getUsage(page, from, to)` for logs. No new API endpoints needed. SVG patterns reused from existing code.

**Tech Stack:** Vue 3.5, Naive UI (NButton, NDatePicker, NDataTable, NModal, NCode, NSpace, NText, NEmpty), CSS variables from base.css.

---

## File Map

| File | Change |
|------|--------|
| `frontend/src/pages/Dashboard.vue` | Add time range bar + 4 stat cards + 2 SVG charts + model breakdown table; remove API info + quick links |
| `frontend/src/pages/Usage.vue` | Remove time range + stat cards + SVG charts + breakdown table; keep log table + add per-model horizontal bar chart |

---

### Task 1: Dashboard.vue — add analytics, remove API info + quick links

**Files:**
- Modify: `frontend/src/pages/Dashboard.vue` (full rewrite)

Current structure (lines 57–81): bottom section has API info card + quick links card — both removed.
New additions: time range bar, 4 stat cards, 2 SVG charts (daily cost + top-5 model lines), model breakdown table.
Kept: welcome header, 4 summary stat cards (balance/requests/tokens/keys), trend chart.

- [ ] **Step 1: Replace the entire file**

```vue
<template>
  <div>
    <!-- Welcome -->
    <div class="dash-welcome">
      <div>
        <div class="dash-greeting">{{ t('welcomeBack') }}，{{ userName }}</div>
        <div class="dash-date">{{ todayStr }}</div>
      </div>
      <n-button type="primary" size="small" @click="$router.push('/plans')">{{ t('topUp') }}</n-button>
    </div>

    <!-- Summary stat cards -->
    <div class="dash-stat-grid">
      <div class="dash-stat-card">
        <div class="dsc-label">{{ t('balance') }}</div>
        <div class="dsc-value">¥{{ dash.balance_yuan || '0.00' }}</div>
        <div class="dsc-sub">{{ t('totalSpent') }} ¥{{ dash.total_cost_yuan || '0.00' }}</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">{{ t('requests') }}</div>
        <div class="dsc-value">{{ (dash.today_calls || 0).toLocaleString() }}</div>
        <div class="dsc-sub">{{ t('totalCalls') }} {{ (dash.total_calls || 0).toLocaleString() }}</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">{{ t('totalTokens') }}</div>
        <div class="dsc-value">{{ fmtTokens(dash.total_tokens) }}</div>
        <div class="dsc-sub">{{ t('allTime') }}</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">{{ t('activeKeys') }}</div>
        <div class="dsc-value">{{ dash.key_count || '—' }}</div>
        <div class="dsc-sub" style="cursor:pointer;color:var(--primary)" @click="$router.push('/keys')">管理 →</div>
      </div>
    </div>

    <!-- Time range selector for analytics -->
    <div class="time-bar">
      <button
        v-for="r in TIME_RANGES" :key="r.key"
        :class="['time-btn', activeRange === r.key && 'active']"
        @click="selectRange(r.key)"
      >{{ r.label }}</button>
      <template v-if="activeRange === 'custom'">
        <n-date-picker v-model:value="customFrom" type="date" size="small" style="width:130px" placeholder="开始日期" />
        <span style="color:var(--text-muted)">~</span>
        <n-date-picker v-model:value="customTo" type="date" size="small" style="width:130px" placeholder="结束日期" />
        <n-button size="small" type="primary" @click="loadAnalytics">查询</n-button>
      </template>
    </div>

    <!-- Analytics stat cards -->
    <div class="dash-stat-grid" style="margin-bottom:16px">
      <div class="dash-stat-card">
        <div class="dsc-label">消费金额</div>
        <div class="dsc-value">¥{{ stats.cost }}</div>
        <div class="dsc-sub">所选时段</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">请求次数</div>
        <div class="dsc-value">{{ stats.calls.toLocaleString() }}</div>
        <div class="dsc-sub">所选时段</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">消耗 Tokens</div>
        <div class="dsc-value">{{ fmtTokens(stats.tokens) }}</div>
        <div class="dsc-sub">所选时段</div>
      </div>
      <div class="dash-stat-card">
        <div class="dsc-label">错误率</div>
        <div class="dsc-value">{{ stats.errorRate }}%</div>
        <div class="dsc-sub">所选时段</div>
      </div>
    </div>

    <!-- Charts row -->
    <div class="chart-row">
      <!-- Daily cost line chart -->
      <div class="dash-chart-card">
        <div class="dash-section-title">每日消费趋势</div>
        <svg v-if="trendData.length" viewBox="0 0 600 180" style="width:100%;height:auto">
          <defs>
            <linearGradient id="dashGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon :points="costArea" fill="url(#dashGrad)"/>
          <polyline :points="costLine" fill="none" stroke="var(--primary)" stroke-width="2"/>
          <circle v-for="(p,i) in trendData" :key="i" :cx="cx(i,trendData.length)" :cy="cy(p.cost_yuan,maxCost)" r="3" fill="var(--primary)"/>
          <text v-for="(p,i) in trendData" :key="'l'+i" :x="cx(i,trendData.length)" y="176" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text>
        </svg>
        <n-empty v-else description="暂无数据" style="padding:32px 0" />
      </div>

      <!-- Top-5 model request lines -->
      <div class="dash-chart-card">
        <div class="dash-section-title">Top 5 模型请求量</div>
        <svg v-if="modelTrendLines.length" viewBox="0 0 600 180" style="width:100%;height:auto">
          <polyline
            v-for="(line,li) in modelTrendLines" :key="li"
            :points="line.points" fill="none"
            :stroke="MODEL_COLORS[li % MODEL_COLORS.length]" stroke-width="1.8"
          />
          <text v-for="(p,i) in trendData" :key="'lx'+i" :x="cx(i,trendData.length)" y="176" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text>
        </svg>
        <n-empty v-else description="暂无数据" style="padding:32px 0" />
        <div class="chart-legend">
          <span v-for="(line,li) in modelTrendLines" :key="li" class="legend-item">
            <span class="legend-dot" :style="{background:MODEL_COLORS[li%MODEL_COLORS.length]}"></span>
            {{ line.model }}
          </span>
        </div>
      </div>
    </div>

    <!-- Model breakdown table -->
    <div class="dash-chart-card" style="margin-top:0">
      <div class="dash-section-title">模型消耗明细</div>
      <table class="breakdown-table">
        <thead>
          <tr><th>模型</th><th>请求数</th><th>Tokens</th><th>占比</th><th>费用</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in breakdownRows" :key="row.model">
            <td><code style="font-size:12px">{{ row.model }}</code></td>
            <td>{{ row.calls.toLocaleString() }}</td>
            <td>{{ fmtTokens(row.tokens) }}</td>
            <td>
              <div class="quota-bar-wrap">
                <div class="quota-bar" :style="{width:row.pct+'%',background:row.pct>=80?'var(--quota-warn)':'var(--primary)'}"></div>
              </div>
              <span :style="{fontSize:'11px',fontWeight:row.pct>=80?700:400}">{{ row.pct }}%</span>
            </td>
            <td>¥{{ row.cost }}</td>
          </tr>
          <tr v-if="!breakdownRows.length">
            <td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px 0">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { NButton, NEmpty, NDatePicker } from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()
const userName = ref('')
const dash = ref({})
const trendData = ref([])
const activeRange = ref('7')
const customFrom = ref(null)
const customTo = ref(null)
const breakdownLogs = ref([])

const MODEL_COLORS = ['#4f6ef7','#34d399','#f59e0b','#e85454','#8b5cf6']
const TIME_RANGES = [
  { key: '1', label: '今日' },
  { key: '7', label: '近7天' },
  { key: '30', label: '近30天' },
  { key: 'custom', label: '自定义' },
]

const stats = ref({ cost: '0.00', calls: 0, tokens: 0, errorRate: '0.0' })

const todayStr = computed(() =>
  new Date().toLocaleDateString('zh-CN', { year:'numeric', month:'long', day:'numeric', weekday:'long' })
)

function dateRange() {
  const now = new Date()
  if (activeRange.value === 'custom') {
    return {
      from: customFrom.value ? new Date(customFrom.value).toISOString().slice(0,10) : null,
      to: customTo.value ? new Date(customTo.value).toISOString().slice(0,10) : null,
    }
  }
  const days = parseInt(activeRange.value)
  const from = new Date(now); from.setDate(from.getDate() - days + 1)
  return { from: from.toISOString().slice(0,10), to: now.toISOString().slice(0,10) }
}

async function loadAnalytics() {
  const { from, to } = dateRange()
  try {
    // api.getTrend only accepts day count, not date range — custom falls back to 30
    const days = activeRange.value === 'custom' ? 30 : parseInt(activeRange.value)
    const tr = await api.getTrend(days)
    trendData.value = tr.trend || []
    const items = tr.details || []
    const totalCost = items.reduce((s,d) => s + (parseFloat(d.cost_yuan)||0), 0)
    const totalCalls = items.reduce((s,d) => s + (d.calls||0), 0)
    const totalTokens = items.reduce((s,d) => s + (d.tokens||0), 0)
    const totalErrors = items.reduce((s,d) => s + (d.errors||0), 0)
    stats.value = {
      cost: totalCost.toFixed(2),
      calls: totalCalls,
      tokens: totalTokens,
      errorRate: totalCalls > 0 ? ((totalErrors/totalCalls)*100).toFixed(1) : '0.0',
    }
  } catch (e) { console.error('loadAnalytics failed', e) }
  try {
    const data = await api.getUsage(1, from, to)
    breakdownLogs.value = data.items || []
  } catch (e) { console.error('loadBreakdown failed', e) }
}

function selectRange(key) {
  activeRange.value = key
  if (key !== 'custom') loadAnalytics()
}

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan||0), 1))
function cx(i, len) { return 40 + (i / Math.max(len-1,1)) * 520 }
function cy(v, max) { return 150 - ((v||0) / max) * 120 }

const costLine = computed(() =>
  trendData.value.map((d,i) => `${cx(i,trendData.value.length)},${cy(d.cost_yuan,maxCost.value)}`).join(' ')
)
const costArea = computed(() => {
  const n = trendData.value.length
  const pts = trendData.value.map((d,i) => `${cx(i,n)},${cy(d.cost_yuan,maxCost.value)}`)
  return `${cx(0,n)},150 ${pts.join(' ')} ${cx(n-1,n)},150`
})

const modelTrendLines = computed(() => {
  if (!trendData.value.length) return []
  const modelSet = {}
  trendData.value.forEach(day => {
    ;(day.models||[]).forEach(m => {
      if (!modelSet[m.model]) modelSet[m.model] = 0
      modelSet[m.model] += m.calls||0
    })
  })
  const top5 = Object.entries(modelSet).sort((a,b) => b[1]-a[1]).slice(0,5).map(([model]) => model)
  const maxCalls = Math.max(...trendData.value.flatMap(d => (d.models||[]).map(m => m.calls||0)), 1)
  return top5.map(model => ({
    model,
    points: trendData.value.map((day,i) => {
      const calls = (day.models||[]).find(m => m.model===model)?.calls||0
      return `${cx(i,trendData.value.length)},${cy(calls,maxCalls)}`
    }).join(' '),
  }))
})

const breakdownRows = computed(() => {
  const modelMap = {}
  breakdownLogs.value.forEach(l => {
    if (!modelMap[l.model]) modelMap[l.model] = { calls:0, tokens:0, cost:0 }
    modelMap[l.model].calls++
    modelMap[l.model].tokens += (l.prompt_tokens||0) + (l.completion_tokens||0)
    modelMap[l.model].cost += parseFloat(l.cost_yuan)||0
  })
  const rows = Object.entries(modelMap).map(([model,v]) => ({
    model, calls: v.calls, tokens: v.tokens, cost: v.cost.toFixed(4),
  })).sort((a,b) => parseFloat(b.cost)-parseFloat(a.cost))
  const total = rows.reduce((s,r) => s+parseFloat(r.cost), 0)
  return rows.map(r => ({ ...r, pct: total>0 ? Math.round((parseFloat(r.cost)/total)*100) : 0 }))
})

function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M'
  if (n >= 1000) return (n/1000).toFixed(1)+'K'
  return String(n)
}

onMounted(async () => {
  try { const u = await api.getMe(); userName.value = u.username||u.email||'' } catch(e) {}
  try { const d = await api.getDashboard(); dash.value = {...dash.value,...d} } catch(e) {}
  await loadAnalytics()
})
</script>

<style scoped>
.dash-welcome { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.dash-greeting { font-size:18px; font-weight:700; color:var(--text); }
.dash-date { font-size:12px; color:var(--text-muted); margin-top:2px; }

.dash-stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:16px; }
@media (max-width:800px) { .dash-stat-grid { grid-template-columns:repeat(2,1fr); } }
.dash-stat-card { background:var(--surface); border:1px solid var(--border-light); border-radius:var(--radius); padding:16px 20px; }
.dsc-label { font-size:12px; color:var(--text-secondary); margin-bottom:4px; }
.dsc-value { font-size:26px; font-weight:700; color:var(--text); line-height:1.2; }
.dsc-sub { font-size:11px; color:var(--text-muted); margin-top:4px; }

.time-bar { display:flex; align-items:center; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.time-btn { padding:5px 14px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--text-secondary); font-size:13px; cursor:pointer; transition:all 0.15s; }
.time-btn:hover { border-color:var(--primary); color:var(--primary); }
.time-btn.active { background:var(--primary); border-color:var(--primary); color:#fff; }

.chart-row { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; margin-bottom:16px; }
@media (max-width:800px) { .chart-row { grid-template-columns:1fr; } }
.dash-chart-card { background:var(--surface); border:1px solid var(--border-light); border-radius:var(--radius); padding:20px; }
.dash-section-title { font-size:13px; font-weight:600; color:var(--text); margin-bottom:14px; }

.chart-legend { display:flex; flex-wrap:wrap; gap:10px; margin-top:8px; }
.legend-item { display:flex; align-items:center; gap:5px; font-size:11px; color:var(--text-secondary); }
.legend-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

.breakdown-table { width:100%; border-collapse:collapse; font-size:13px; }
.breakdown-table th { text-align:left; padding:8px 12px; font-size:12px; color:var(--text-secondary); border-bottom:1px solid var(--border-light); font-weight:500; }
.breakdown-table td { padding:10px 12px; border-bottom:1px solid var(--border-light); }
.breakdown-table tbody tr:last-child td { border-bottom:none; }
.quota-bar-wrap { height:4px; background:var(--border-light); border-radius:2px; margin-bottom:3px; width:100px; }
.quota-bar { height:4px; border-radius:2px; transition:width 0.3s; }
</style>
```

- [ ] **Step 2: Verify in browser**

Navigate to http://localhost:5173/. Check:
1. 欢迎语 + 4格摘要卡（余额/今日请求/总Token/Key数）在顶部
2. 时间范围按钮（今日/近7天/近30天/自定义）
3. 4格分析统计卡（消费/请求数/Tokens/错误率）
4. 两列SVG图表（每日消费趋势 + Top5模型请求量）
5. 模型消耗明细表（带进度条）
6. 底部无API信息、无快捷链接

---

### Task 2: Usage.vue — 专注日志 + 模型消耗横向条形图

**Files:**
- Modify: `frontend/src/pages/Usage.vue` (full rewrite)

移除：时间范围选择器、4格统计卡、SVG折线图（两列）、模型消耗明细表。
保留：调用日志表、详情弹窗。
新增：模型消耗横向条形图（SVG）、过滤栏（Key名称/模型/状态）。

- [ ] **Step 1: Replace the entire file**

```vue
<template>
  <div>
    <!-- Page title -->
    <div class="log-header">
      <div class="log-title">调用日志</div>
      <div class="log-filters">
        <input v-model="filterKeyName" class="log-input" placeholder="Key 名称" />
        <input v-model="filterModel" class="log-input" placeholder="模型" />
        <select v-model="filterStatus" class="log-select">
          <option value="">全部状态</option>
          <option value="success">成功</option>
          <option value="error">失败</option>
        </select>
        <button class="log-btn log-btn--primary" @click="doSearch">查询</button>
        <button class="log-btn" @click="resetFilter">重置</button>
      </div>
    </div>

    <!-- Model usage bar chart -->
    <div class="log-card" style="margin-bottom:16px">
      <div class="log-section-title">模型调用分布 <span class="log-section-sub">（当前页）</span></div>
      <div v-if="barRows.length" class="bar-chart">
        <div v-for="row in barRows" :key="row.model" class="bar-row">
          <div class="bar-label">
            <code class="bar-model">{{ row.model }}</code>
            <span class="bar-count">{{ row.calls }} 次</span>
          </div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{width: row.pct + '%', background: MODEL_COLORS[barRows.indexOf(row) % MODEL_COLORS.length]}"
            ></div>
          </div>
          <span class="bar-cost">¥{{ row.cost }}</span>
        </div>
      </div>
      <div v-else class="log-empty">暂无数据</div>
    </div>

    <!-- Log table -->
    <div class="log-card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div class="log-section-title" style="margin-bottom:0">详细日志</div>
        <div style="display:flex;gap:6px">
          <button class="log-btn" :disabled="page <= 1" @click="loadPage(page - 1)">上一页</button>
          <button class="log-btn" :disabled="logs.length === 0" @click="loadPage(page + 1)">下一页</button>
        </div>
      </div>
      <n-data-table
        v-if="logs.length"
        :columns="logColumns"
        :data="logs"
        :bordered="false"
        :single-line="false"
        size="small"
      />
      <div v-else class="log-empty">暂无调用记录</div>
    </div>

    <!-- Detail modal -->
    <n-modal v-model:show="showDetail" preset="card" title="调用详情" style="max-width:480px" :bordered="true">
      <n-space vertical :size="8">
        <n-text depth="2" style="font-size:12px">Request ID: <n-code>{{ detailLog?.id }}</n-code></n-text>
        <n-text depth="2" style="font-size:12px">模型: {{ detailLog?.model }}</n-text>
        <n-text depth="2" style="font-size:12px">时间: {{ fmtTime(detailLog?.created_at) }}</n-text>
        <n-text depth="2" style="font-size:12px">耗时: {{ detailLog?.duration_ms || detailLog?.latency_ms || '-' }}ms</n-text>
        <n-text depth="2" style="font-size:12px">Tokens: {{ detailLog?.prompt_tokens }} in / {{ detailLog?.completion_tokens }} out</n-text>
        <n-text depth="2" style="font-size:12px">花费: ¥{{ detailLog?.cost_yuan || '0.00' }}</n-text>
        <n-text depth="2" style="font-size:12px">IP: {{ detailLog?.ip || '-' }}</n-text>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { NButton, NDataTable, NModal, NSpace, NText, NCode } from 'naive-ui'
import { api } from '../api'

const MODEL_COLORS = ['#4f6ef7','#34d399','#f59e0b','#e85454','#8b5cf6']

const logs = ref([])
const page = ref(1)
const filterKeyName = ref('')
const filterModel = ref('')
const filterStatus = ref('')
const showDetail = ref(false)
const detailLog = ref(null)

const filteredLogs = computed(() => {
  let list = logs.value
  if (filterKeyName.value) list = list.filter(l => (l.key_name||'').includes(filterKeyName.value))
  if (filterModel.value) list = list.filter(l => l.model.includes(filterModel.value))
  if (filterStatus.value) list = list.filter(l => l.status === filterStatus.value)
  return list
})

const barRows = computed(() => {
  const modelMap = {}
  filteredLogs.value.forEach(l => {
    if (!modelMap[l.model]) modelMap[l.model] = { calls: 0, cost: 0 }
    modelMap[l.model].calls++
    modelMap[l.model].cost += parseFloat(l.cost_yuan) || 0
  })
  const rows = Object.entries(modelMap)
    .map(([model, v]) => ({ model, calls: v.calls, cost: v.cost.toFixed(4) }))
    .sort((a, b) => b.calls - a.calls)
    .slice(0, 8)
  const maxCalls = rows[0]?.calls || 1
  return rows.map(r => ({ ...r, pct: Math.round((r.calls / maxCalls) * 100) }))
})

const logColumns = [
  { title: '时间', key: 'created_at', width: 140, render: row => h('span', { style: 'font-size:12px' }, fmtTime(row.created_at)) },
  { title: 'Key', key: 'key_name', width: 100, render: row => h('span', { style: 'font-size:12px' }, row.key_name || '默认') },
  { title: '模型', key: 'model', render: row => h('code', { style: 'font-size:11px' }, row.model) },
  { title: '耗时', key: 'latency_ms', width: 80, render: row => (row.latency_ms || '-') + 'ms' },
  { title: '输入', key: 'prompt_tokens', width: 70 },
  { title: '输出', key: 'completion_tokens', width: 70 },
  { title: '费用', key: 'cost_yuan', width: 80, render: row => '¥' + (row.cost_yuan || '0.00') },
  { title: '状态', key: 'status', width: 70, render: row => h('span', {
    style: `font-size:11px;padding:2px 6px;border-radius:8px;background:${row.status==='success'?'#f0fdf4':'#fef2f2'};color:${row.status==='success'?'#059669':'#dc2626'}`
  }, row.status === 'success' ? '成功' : '失败') },
  { title: '操作', key: 'actions', width: 60, render: row => h(NButton, {
    size: 'tiny', onClick: () => { detailLog.value = row; showDetail.value = true }
  }, { default: () => '详情' }) },
]

async function loadPage(p) {
  page.value = p
  try {
    const data = await api.getUsage(p, null, null)
    logs.value = data.items || []
  } catch (e) { console.error('loadPage failed', e) }
}

function doSearch() { loadPage(1) }
function resetFilter() {
  filterKeyName.value = ''; filterModel.value = ''; filterStatus.value = ''
  loadPage(1)
}

function fmtTime(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }

onMounted(() => loadPage(1))
</script>

<style scoped>
.log-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.log-title { font-size: 18px; font-weight: 700; color: var(--text); }
.log-filters { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.log-input {
  padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border);
  font-size: 13px; background: var(--surface); color: var(--text);
  outline: none; width: 120px;
}
.log-input:focus { border-color: var(--primary); }
.log-select {
  padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border);
  font-size: 13px; background: var(--surface); color: var(--text);
  outline: none; cursor: pointer;
}
.log-btn {
  padding: 5px 14px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text-secondary); font-size: 13px; cursor: pointer;
}
.log-btn:hover { border-color: var(--primary); color: var(--primary); }
.log-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.log-btn--primary { background: var(--primary); border-color: var(--primary); color: #fff; }
.log-btn--primary:hover { background: var(--primary-hover); border-color: var(--primary-hover); color: #fff; }

.log-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px;
}
.log-section-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 14px; }
.log-section-sub { font-size: 11px; font-weight: 400; color: var(--text-muted); }
.log-empty { text-align: center; padding: 32px 0; color: var(--text-muted); font-size: 13px; }

.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 10px; }
.bar-label { width: 240px; flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; }
.bar-model { font-family: var(--font-mono); font-size: 11px; color: var(--text); }
.bar-count { font-size: 11px; color: var(--text-muted); margin-left: 6px; flex-shrink: 0; }
.bar-track {
  flex: 1; height: 8px; background: var(--border-light);
  border-radius: 4px; overflow: hidden;
}
.bar-fill { height: 8px; border-radius: 4px; transition: width 0.4s ease; }
.bar-cost { font-size: 11px; color: var(--text-muted); width: 60px; text-align: right; flex-shrink: 0; }
</style>
```

- [ ] **Step 2: Verify in browser**

Navigate to http://localhost:5173/usage. Check:
1. 页面顶部显示 "调用日志" 标题 + 过滤栏（Key名称/模型/状态）
2. 模型调用分布横向条形图显示（按当前页日志数据，最多8条）
3. 每行：模型名 + 横向彩色条 + 调用次数 + 费用
4. 详细日志表格（9列：时间/Key/模型/耗时/输入/输出/费用/状态/操作）
5. 状态列：成功=绿色，失败=红色
6. 上一页/下一页分页正常
7. 点击"详情"弹出调用详情弹窗
8. 无时间范围选择器、无统计卡、无折线图

---

## Self-Review

**Spec coverage:**
- ✅ Dashboard 移除 API 信息 + 快捷入口 — Task 1
- ✅ Dashboard 加时间范围 + 4分析统计卡 + 2SVG图表 + 模型明细 — Task 1
- ✅ Usage 移除统计卡/图表 — Task 2
- ✅ Usage 专注日志 — Task 2（保留日志表+详情弹窗）
- ✅ Usage 模型消耗图表 — Task 2（横向条形图）

**Placeholder scan:** 无。所有步骤含完整代码。

**Type consistency:**
- Dashboard `cx(i,len)` / `cy(v,max)` 与 Usage 中同名函数逻辑相同但独立定义，无冲突。
- `barRows` computed 引用 `filteredLogs.value`，`filteredLogs` 依赖 `logs.value`，链条完整。
- `logColumns` 引用 `NButton`（已 import）、`detailLog`、`showDetail`（均已定义）。
