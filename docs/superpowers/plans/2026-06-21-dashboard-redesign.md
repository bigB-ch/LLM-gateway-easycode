# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Dashboard.vue to match the TokenHub visual style used by the other three pages — 4 stat cards, full-width trend chart, API info + quick links row at bottom. Remove announcements and FAQ.

**Architecture:** Single file rewrite of `Dashboard.vue`. Keeps all existing API calls (`api.getDashboard`, `api.getTrend`, `api.getMe`). Removes `api.getAnnouncements` and `api.getFAQ` calls. SVG chart logic unchanged. Visual style matches `Usage.vue` stat cards and `base.css` card pattern.

**Tech Stack:** Vue 3.5, Naive UI (NButton, NEmpty only), CSS variables from base.css, existing api.js.

---

### Task 1: Rewrite Dashboard.vue

**Files:**
- Modify: `frontend/src/pages/Dashboard.vue` (full rewrite)

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

    <!-- Stat cards -->
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
        <div class="dsc-sub" style="cursor:pointer;color:var(--primary)" @click="$router.push('/keys')">{{ t('tokens') }} →</div>
      </div>
    </div>

    <!-- Trend chart -->
    <div class="dash-chart-card">
      <div class="dash-section-title">{{ t('spendingTrend') }} <span style="font-size:11px;font-weight:400;color:var(--text-muted)">近 7 天</span></div>
      <svg v-if="trendData.length" viewBox="0 0 600 180" style="width:100%;height:auto">
        <defs>
          <linearGradient id="dashGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <polygon :points="chartArea" fill="url(#dashGrad)"/>
        <polyline :points="chartPoints" fill="none" stroke="var(--primary)" stroke-width="2"/>
        <circle v-for="(p,i) in trendData" :key="i" :cx="x(i)" :cy="y(p.cost_yuan)" r="3" fill="var(--primary)"/>
        <text v-for="(p,i) in trendData" :key="'l'+i" :x="x(i)" y="176" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text>
      </svg>
      <n-empty v-else :description="t('trendHint')" style="padding:32px 0" />
    </div>

    <!-- Bottom row: API info + Quick links -->
    <div class="dash-bottom-grid">
      <div class="dash-info-card">
        <div class="dash-section-title">{{ t('apiInfo') }}</div>
        <div class="info-row">
          <span class="info-label">Base URL</span>
          <code class="info-code">https://easycode.uno/v1</code>
        </div>
        <div class="info-row">
          <span class="info-label">Auth</span>
          <code class="info-code">Bearer sk-...</code>
        </div>
        <div class="info-row">
          <span class="info-label">Format</span>
          <span style="font-size:13px;color:var(--text)">OpenAI Compatible</span>
        </div>
      </div>
      <div class="dash-info-card">
        <div class="dash-section-title">{{ t('quickLinks') }}</div>
        <div class="quick-link" @click="$router.push('/keys')">{{ t('createKey') }} →</div>
        <div class="quick-link" @click="$router.push('/playground')">{{ t('testPlayground') }} →</div>
        <div class="quick-link" @click="$router.push('/models')">{{ t('browseModels') }} →</div>
        <div class="quick-link" @click="$router.push('/usage')">{{ t('usage') }} →</div>
      </div>
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
const trendData = ref([])

const todayStr = computed(() => new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }))

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))
function x(i) { return 40 + (i / Math.max(trendData.value.length - 1, 1)) * 520 }
function y(v) { return 150 - ((v || 0) / maxCost.value) * 120 }
const chartPoints = computed(() => trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' '))
const chartArea = computed(() =>
  `${x(0)},150 ` + trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' ') +
  ` ${x(Math.max(trendData.value.length - 1, 0))},150`
)

function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

onMounted(async () => {
  try { const u = await api.getMe(); userName.value = u.username || u.email || '' } catch (e) { /* */ }
  try { const d = await api.getDashboard(); dash.value = { ...dash.value, ...d } } catch (e) { /* */ }
  try { const tr = await api.getTrend(7); trendData.value = tr.trend || [] } catch (e) { /* */ }
})
</script>

<style scoped>
.dash-welcome {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.dash-greeting { font-size: 18px; font-weight: 700; color: var(--text); }
.dash-date { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.dash-stat-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  margin-bottom: 16px;
}
@media (max-width: 800px) { .dash-stat-grid { grid-template-columns: repeat(2, 1fr); } }

.dash-stat-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px 20px;
}
.dsc-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.dsc-value { font-size: 26px; font-weight: 700; color: var(--text); line-height: 1.2; }
.dsc-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.dash-chart-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px;
  margin-bottom: 16px;
}
.dash-section-title {
  font-size: 13px; font-weight: 600; color: var(--text);
  margin-bottom: 14px;
}

.dash-bottom-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;
}
@media (max-width: 600px) { .dash-bottom-grid { grid-template-columns: 1fr; } }

.dash-info-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px;
}
.info-row {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 0; border-bottom: 1px solid var(--border-light);
}
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 12px; color: var(--text-secondary); width: 70px; flex-shrink: 0; }
.info-code {
  font-family: var(--font-mono); font-size: 12px;
  background: var(--primary-light); color: var(--primary);
  padding: 2px 8px; border-radius: 4px;
}

.quick-link {
  padding: 10px 0; font-size: 13px; color: var(--primary);
  cursor: pointer; border-bottom: 1px solid var(--border-light);
}
.quick-link:last-child { border-bottom: none; }
.quick-link:hover { color: var(--primary-hover); }
</style>
```

- [ ] **Step 2: Verify in browser**

Navigate to http://localhost:5173/. Check:
1. 欢迎语 + 今日日期在顶部，右边有"充值"按钮
2. 4格统计卡：余额 / 今日请求数 / 总 Token / 有效 Key 数
3. 消费趋势折线图（全宽），无数据时显示空状态
4. 底部两列：API 信息（Base URL / Auth / Format）+ 快捷链接（4条）
5. 公告和 FAQ 已不存在

- [ ] **Step 3: No git commit** (not a git repo)
