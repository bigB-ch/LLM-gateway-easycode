<template>
  <div>
    <!-- Time range selector -->
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
        <n-button size="small" type="primary" @click="loadAll">查询</n-button>
      </template>
    </div>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card-item" style="background:var(--card-yellow-bg);border-left:3px solid var(--card-yellow-accent)">
        <div class="sci-label">消费金额</div>
        <div class="sci-value">¥{{ stats.cost }}</div>
        <div class="sci-sub">所选时段</div>
      </div>
      <div class="stat-card-item" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
        <div class="sci-label">请求次数</div>
        <div class="sci-value">{{ stats.calls.toLocaleString() }}</div>
        <div class="sci-sub">所选时段</div>
      </div>
      <div class="stat-card-item" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
        <div class="sci-label">消耗 Tokens</div>
        <div class="sci-value">{{ fmtTokens(stats.tokens) }}</div>
        <div class="sci-sub">所选时段</div>
      </div>
      <div class="stat-card-item" style="background:var(--card-red-bg);border-left:3px solid var(--card-red-accent)">
        <div class="sci-label">错误率</div>
        <div class="sci-value">{{ stats.errorRate }}%</div>
        <div class="sci-sub">所选时段</div>
      </div>
    </div>

    <!-- Header + filters -->
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

    <!-- Model call distribution bar chart -->
    <div class="log-card" style="margin-bottom:16px">
      <div class="log-section-title">
        模型调用分布
        <span class="log-section-sub">（当前页）</span>
      </div>
      <div v-if="barRows.length" class="bar-chart">
        <div v-for="(row, idx) in barRows" :key="row.model" class="bar-row">
          <div class="bar-label">
            <code class="bar-model">{{ row.model }}</code>
            <span class="bar-count">{{ row.calls }} 次</span>
          </div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{width: row.pct + '%', background: MODEL_COLORS[idx % MODEL_COLORS.length]}"
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
        v-if="filteredLogs.length"
        :columns="logColumns"
        :data="filteredLogs"
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
import { NButton, NDataTable, NDatePicker, NModal, NSpace, NText, NCode } from 'naive-ui'
import { api } from '../api'

const MODEL_COLORS = ['#4f6ef7','#34d399','#f59e0b','#e85454','#8b5cf6']

const TIME_RANGES = [
  { key: '1', label: '今日' },
  { key: '7', label: '近7天' },
  { key: '30', label: '近30天' },
  { key: 'custom', label: '自定义' },
]

const activeRange = ref('7')
const customFrom = ref(null)
const customTo = ref(null)
const logs = ref([])
const page = ref(1)
const filterKeyName = ref('')
const filterModel = ref('')
const filterStatus = ref('')
const showDetail = ref(false)
const detailLog = ref(null)
const stats = ref({ cost: '0.00', calls: 0, tokens: 0, errorRate: '0.0' })

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

async function loadAll() {
  const { from, to } = dateRange()
  try {
    // api.getTrend only accepts day count — custom range falls back to 30
    const days = activeRange.value === 'custom' ? 30 : parseInt(activeRange.value)
    const tr = await api.getTrend(days)
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
  } catch (e) { console.error('loadStats failed', e) }
  await loadPage(1, from, to)
}

function selectRange(key) {
  activeRange.value = key
  if (key !== 'custom') loadAll()
}

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

async function loadPage(p, from, to) {
  page.value = p
  const range = (from !== undefined) ? { from, to } : dateRange()
  try {
    const data = await api.getUsage(p, range.from, range.to)
    logs.value = data.items || []
  } catch (e) { console.error('loadPage failed', e) }
}

function doSearch() { loadAll() }
function resetFilter() {
  filterKeyName.value = ''; filterModel.value = ''; filterStatus.value = ''
  loadAll()
}

function fmtTime(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }
function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M'
  if (n >= 1000) return (n/1000).toFixed(1)+'K'
  return String(n)
}

onMounted(() => loadAll())
</script>

<style scoped>
.time-bar { display:flex; align-items:center; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.time-btn { padding:5px 14px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--text-secondary); font-size:13px; cursor:pointer; transition:all 0.15s; }
.time-btn:hover { border-color:var(--primary); color:var(--primary); }
.time-btn.active { background:var(--primary); border-color:var(--primary); color:#fff; }

.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
@media (max-width:800px) { .stat-grid { grid-template-columns:repeat(2,1fr); } }
.stat-card-item { background:var(--surface); border:1px solid var(--border-light); border-radius:var(--radius); padding:16px 20px; }
.sci-label { font-size:12px; color:var(--text-secondary); margin-bottom:4px; }
.sci-value { font-size:24px; font-weight:700; color:var(--text); line-height:1.2; }
.sci-sub { font-size:11px; color:var(--text-muted); margin-top:4px; }

.log-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; flex-wrap:wrap; gap:10px; }
.log-title { font-size:15px; font-weight:700; color:var(--text); }
.log-filters { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.log-input { padding:5px 10px; border-radius:6px; border:1px solid var(--border); font-size:13px; background:var(--surface); color:var(--text); outline:none; width:120px; }
.log-input:focus { border-color:var(--primary); }
.log-select { padding:5px 10px; border-radius:6px; border:1px solid var(--border); font-size:13px; background:var(--surface); color:var(--text); outline:none; cursor:pointer; }
.log-btn { padding:5px 14px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--text-secondary); font-size:13px; cursor:pointer; }
.log-btn:hover { border-color:var(--primary); color:var(--primary); }
.log-btn:disabled { opacity:0.4; cursor:not-allowed; }
.log-btn--primary { background:var(--primary); border-color:var(--primary); color:#fff; }
.log-btn--primary:hover { background:var(--primary-hover); border-color:var(--primary-hover); color:#fff; }

.log-card { background:var(--surface); border:1px solid var(--border-light); border-radius:var(--radius); padding:20px; }
.log-section-title { font-size:13px; font-weight:600; color:var(--text); margin-bottom:14px; }
.log-section-sub { font-size:11px; font-weight:400; color:var(--text-muted); }
.log-empty { text-align:center; padding:32px 0; color:var(--text-muted); font-size:13px; }

.bar-chart { display:flex; flex-direction:column; gap:10px; }
.bar-row { display:flex; align-items:center; gap:10px; }
.bar-label { width:240px; flex-shrink:0; display:flex; align-items:center; justify-content:space-between; }
.bar-model { font-family:var(--font-mono); font-size:11px; color:var(--text); }
.bar-count { font-size:11px; color:var(--text-muted); margin-left:6px; flex-shrink:0; }
.bar-track { flex:1; height:8px; background:var(--border-light); border-radius:4px; overflow:hidden; }
.bar-fill { height:8px; border-radius:4px; transition:width 0.4s ease; }
.bar-cost { font-size:11px; color:var(--text-muted); width:60px; text-align:right; flex-shrink:0; }
</style>
