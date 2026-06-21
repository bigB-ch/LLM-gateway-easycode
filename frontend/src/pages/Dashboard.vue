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
      <div class="dash-stat-card" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
        <div class="dsc-label">{{ t('balance') }}</div>
        <div class="dsc-value">¥{{ dash.balance_yuan || '0.00' }}</div>
        <div class="dsc-sub">{{ t('totalSpent') }} ¥{{ dash.total_cost_yuan || '0.00' }}</div>
      </div>
      <div class="dash-stat-card" style="background:var(--card-green-bg);border-left:3px solid var(--card-green-accent)">
        <div class="dsc-label">{{ t('requests') }}</div>
        <div class="dsc-value">{{ (dash.today_calls || 0).toLocaleString() }}</div>
        <div class="dsc-sub">{{ t('totalCalls') }} {{ (dash.total_calls || 0).toLocaleString() }}</div>
      </div>
      <div class="dash-stat-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
        <div class="dsc-label">{{ t('totalTokens') }}</div>
        <div class="dsc-value">{{ fmtTokens(dash.total_tokens) }}</div>
        <div class="dsc-sub">{{ t('allTime') }}</div>
      </div>
      <div class="dash-stat-card" style="background:var(--card-yellow-bg);border-left:3px solid var(--card-yellow-accent)">
        <div class="dsc-label">{{ t('activeKeys') }}</div>
        <div class="dsc-value">{{ dash.key_count || '—' }}</div>
        <div class="dsc-sub" style="cursor:pointer;color:var(--primary)" @click="$router.push('/keys')">管理 →</div>
      </div>
    </div>

    <!-- Row 2: two line charts -->
    <div class="chart-row">

      <!-- Daily cost line chart -->
      <div class="dash-chart-card">
        <div class="dash-section-title" style="color:var(--card-blue-accent)">每日消费趋势 <span class="chart-sub" style="color:var(--text-muted)">近 7 天</span></div>
        <svg v-if="details.length" viewBox="0 0 560 160" style="width:100%;height:auto">
          <defs>
            <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon :points="costArea" fill="url(#costGrad)"/>
          <polyline :points="costLine" fill="none" stroke="var(--primary)" stroke-width="2"/>
          <circle v-for="(p,i) in details" :key="i" :cx="lx(i,details.length)" :cy="ly(p.cost_yuan,maxCost)" r="3" fill="var(--primary)"/>
          <text v-for="(p,i) in details" :key="'d'+i" :x="lx(i,details.length)" y="157" text-anchor="middle" fill="#aaa" font-size="9">{{ p.date.slice(5) }}</text>
        </svg>
        <n-empty v-else :description="t('trendHint')" style="padding:24px 0" />
      </div>

      <!-- Daily token line chart -->
      <div class="dash-chart-card">
        <div class="dash-section-title" style="color:var(--card-green-accent)">每日 Token 消耗 <span class="chart-sub" style="color:var(--text-muted)">近 7 天</span></div>
        <svg v-if="details.length" viewBox="0 0 560 160" style="width:100%;height:auto">
          <defs>
            <linearGradient id="tokenGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#34d399" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="#34d399" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon :points="tokenArea" fill="url(#tokenGrad)"/>
          <polyline :points="tokenLine" fill="none" stroke="#34d399" stroke-width="2"/>
          <circle v-for="(p,i) in details" :key="i" :cx="lx(i,details.length)" :cy="ly(p.tokens,maxTokens)" r="3" fill="#34d399"/>
          <text v-for="(p,i) in details" :key="'t'+i" :x="lx(i,details.length)" y="157" text-anchor="middle" fill="#aaa" font-size="9">{{ p.date.slice(5) }}</text>
        </svg>
        <n-empty v-else description="暂无数据" style="padding:24px 0" />
      </div>

    </div>

    <!-- Row 3: model usage bar chart (full width) -->
    <div class="dash-chart-card" style="margin-top:16px">
      <div class="dash-section-title" style="color:var(--card-blue-accent)">模型使用量 <span class="chart-sub" style="color:var(--text-muted)">近 7 天</span></div>
      <svg v-if="modelBarData.length" viewBox="0 0 1100 160" style="width:100%;height:auto">
        <g v-for="(m, i) in modelBarData" :key="m.model">
          <rect
            :x="bx(i, modelBarData.length)"
            :y="by(m.calls, maxBarCalls)"
            :width="bw(modelBarData.length)"
            :height="bh(m.calls, maxBarCalls)"
            :fill="MODEL_COLORS[i % MODEL_COLORS.length]"
            rx="3"
          />
          <text :x="bx(i,modelBarData.length)+bw(modelBarData.length)/2" y="157" text-anchor="middle" fill="#aaa" font-size="10">{{ shortModel(m.model) }}</text>
          <text :x="bx(i,modelBarData.length)+bw(modelBarData.length)/2" :y="by(m.calls,maxBarCalls)-4" text-anchor="middle" fill="#888" font-size="10">{{ m.calls }}</text>
        </g>
      </svg>
      <n-empty v-else description="暂无数据" style="padding:24px 0" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { NButton, NEmpty } from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()
const userName = ref('')
const dash = ref({})
const trendData = ref([])   // [{date, cost_yuan}]
const details = ref([])      // [{date, calls, tokens, cost_yuan}]

const MODEL_COLORS = ['#4f6ef7','#34d399','#f59e0b','#e85454','#8b5cf6','#06b6d4','#ec4899']

const todayStr = computed(() =>
  new Date().toLocaleDateString('zh-CN', { year:'numeric', month:'long', day:'numeric', weekday:'long' })
)

// --- Line chart helpers (viewBox 560x160, usable y: 10-148) ---
function lx(i, len) { return 30 + (i / Math.max(len-1,1)) * 500 }
function ly(v, max) { return 148 - ((v||0) / max) * 120 }

const maxCost = computed(() => Math.max(...details.value.map(d => d.cost_yuan||0), 0.01))
const maxTokens = computed(() => Math.max(...details.value.map(d => d.tokens||0), 1))

const costLine = computed(() => details.value.map((d,i) => `${lx(i,details.value.length)},${ly(d.cost_yuan,maxCost.value)}`).join(' '))
const costArea = computed(() => {
  const n = details.value.length
  const pts = details.value.map((d,i) => `${lx(i,n)},${ly(d.cost_yuan,maxCost.value)}`)
  return `${lx(0,n)},148 ${pts.join(' ')} ${lx(n-1,n)},148`
})
const tokenLine = computed(() => details.value.map((d,i) => `${lx(i,details.value.length)},${ly(d.tokens,maxTokens.value)}`).join(' '))
const tokenArea = computed(() => {
  const n = details.value.length
  const pts = details.value.map((d,i) => `${lx(i,n)},${ly(d.tokens,maxTokens.value)}`)
  return `${lx(0,n)},148 ${pts.join(' ')} ${lx(n-1,n)},148`
})

// --- Bar chart helpers (viewBox 560x160, usable y: 10-148) ---
function bw(n) { return Math.max(16, Math.min(56, 480 / Math.max(n,1) * 0.6)) }
function bx(i, n) {
  const w = bw(n); const gap = bw(n) * 0.5
  const total = n * w + (n-1) * gap
  return 30 + i * (w + gap) + Math.max(0, (500 - total) / 2)
}
function by(v, max) { return 148 - (v / max) * 120 }
function bh(v, max) { return (v / max) * 120 }

const maxBarCalls = computed(() => Math.max(...modelBarData.value.map(m => m.calls), 1))

const modelBarData = computed(() => {
  const modelSet = {}
  trendData.value.forEach(day => {
    ;(day.models||[]).forEach(m => {
      if (!modelSet[m.model]) modelSet[m.model] = 0
      modelSet[m.model] += m.calls||0
    })
  })
  return Object.entries(modelSet)
    .map(([model, calls]) => ({ model, calls }))
    .sort((a,b) => b.calls - a.calls)
})

function shortModel(id) {
  const parts = id.split('-')
  if (parts.length <= 2) return id
  return parts.slice(-2).join('-')
}

function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M'
  if (n >= 1000) return (n/1000).toFixed(1)+'K'
  return String(n)
}

onMounted(async () => {
  try { const u = await api.getMe(); userName.value = u.username||u.email||'' } catch(e) {}
  try { const d = await api.getDashboard(); dash.value = {...dash.value,...d} } catch(e) {}
  try {
    const tr = await api.getTrend(7)
    trendData.value = tr.trend || []
    details.value = tr.details || []
  } catch(e) {}
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

.chart-row { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }
@media (max-width:800px) { .chart-row { grid-template-columns:1fr; } }
.dash-chart-card { background:var(--surface); border:1px solid var(--border-light); border-radius:var(--radius); padding:20px; }
.dash-section-title { font-size:13px; font-weight:600; color:var(--text); margin-bottom:14px; }
.chart-sub { font-size:11px; font-weight:400; color:var(--text-muted); margin-left:4px; }
</style>
