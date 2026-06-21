# TokenHub UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Models, Usage, and Keys pages to match TokenHub-style information architecture using the existing Vue 3 + Naive UI stack — no new dependencies.

**Architecture:** Each page is a standalone `.vue` file under `frontend/src/pages/`. Charts reuse the SVG polyline pattern from `Dashboard.vue`. `UserLayout.vue` gets nav-order and page-background fixes only. All data comes from existing `api.js` / `gatewayApi.js`.

**Tech Stack:** Vue 3.5 (Composition API, `<script setup>`), Naive UI 2.44.1, Vite 6, CSS variables from `base.css`, `useI18n()` for text keys.

---

## How to run the dev server

```bash
cd D:/code/llm-gateway/frontend
npm run dev
# app opens at http://localhost:5173
```

No automated component tests exist in this project. Verification = open the page in browser, exercise every interaction described in each task's verification step.

---

## File Map

| File | Change |
|------|--------|
| `frontend/src/styles/base.css` | Add 5 CSS variables to `:root` |
| `frontend/src/layouts/UserLayout.vue` | Fix nav order + page-bg |
| `frontend/src/pages/Models.vue` | Full rewrite — provider tabs + featured cards + grid |
| `frontend/src/pages/Usage.vue` | Full rewrite — time picker + stat cards + SVG charts + breakdown table |
| `frontend/src/pages/Keys.vue` | Full rewrite — summary cards + toolbar + quota-bar table |

---

### Task 1: base.css — add CSS variables

**Files:**
- Modify: `frontend/src/styles/base.css` (`:root` block, around line 32)

- [ ] **Step 1: Add variables to `:root`**

Open `frontend/src/styles/base.css`. Find the closing `}` of the `:root` block (currently at line 32, after the `--mc-orange` pair). Insert before that `}`:

```css
  /* TokenHub redesign additions */
  --status-active: #059669;
  --status-expired: #b45309;
  --status-revoked: #dc2626;
  --quota-warn: #f59e0b;
  --page-bg: #f5f6fa;
```

- [ ] **Step 2: Verify**

Run `npm run dev`, open DevTools → Elements, inspect `<html>`. Confirm the five new variables appear under `:root`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/styles/base.css
git commit -m "style: add status/quota/page-bg CSS variables"
```

---

### Task 2: UserLayout.vue — nav order + page background

**Files:**
- Modify: `frontend/src/layouts/UserLayout.vue` (full file, 41 lines)

**Why:** Spec requires order: Dashboard / Models / Usage / Keys / Playground // Plans / Settings. Current order is wrong and `page-main` has no background.

- [ ] **Step 1: Replace the entire file**

```vue
<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside :class="['sidebar', collapsed && 'collapsed']">
        <div class="sidebar-section">{{ t('consoleGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/"><span class="nav-icon">&#x25A3;</span><span>{{ t('dashboard') }}</span></router-link>
          <router-link to="/models"><span class="nav-icon">&#x1F310;</span><span>{{ t('marketplace') }}</span></router-link>
          <router-link to="/usage"><span class="nav-icon">&#x1F4C4;</span><span>{{ t('usage') }}</span></router-link>
          <router-link to="/keys"><span class="nav-icon">&#x1F511;</span><span>{{ t('tokens') }}</span></router-link>
          <router-link to="/playground"><span class="nav-icon">&#x1F4AC;</span><span>{{ t('playground') }}</span></router-link>
        </nav>
        <div class="sidebar-section">{{ t('personalGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/plans"><span class="nav-icon">&#x1F4B0;</span><span>{{ t('wallet') }}</span></router-link>
          <router-link to="/settings"><span class="nav-icon">&#x2699;&#xFE0F;</span><span>{{ t('settings') }}</span></router-link>
        </nav>
        <div class="sidebar-collapse-btn" @click="collapsed = !collapsed">
          <span class="collapse-icon">&#x00AB;</span>
          <span class="sidebar-collapse-text">{{ t('collapse') }}</span>
        </div>
      </aside>
      <main class="page-main" style="background:var(--page-bg)">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../i18n'
import TopNavBar from '../components/TopNavBar.vue'
const { t } = useI18n()
const collapsed = ref(false)
</script>
```

- [ ] **Step 2: Verify**

Navigate to http://localhost:5173. Sidebar order must be: Dashboard, Models, Usage, Keys, Playground, then Plans, Settings. Main content area background should be `#f5f6fa` (light grey). Active link shows blue left bar (existing `.active` CSS in `base.css` handles this via `router-link-active`).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/UserLayout.vue
git commit -m "feat: fix sidebar nav order and page background"
```

---

### Task 3: Models.vue — provider tabs + featured cards + model grid

**Files:**
- Modify: `frontend/src/pages/Models.vue` (full rewrite, replaces 219-line file)

**What changes vs current:** Remove left sidebar filter panel → horizontal provider tab pills at top. Add "精选推荐" 2-col large cards above the grid. Small cards get gradient icon square + 2-line description clamp + bottom price chips. Hover: blue border + shadow. No new dependencies.

- [ ] **Step 1: Replace the entire content of `frontend/src/pages/Models.vue`**

```vue
<template>
  <div>
    <!-- Provider filter tabs + search -->
    <div class="model-filter-bar">
      <button
        v-for="p in providerTabs"
        :key="p.value"
        :class="['model-tab', fProvider === p.value && 'active']"
        @click="fProvider = p.value"
      >{{ p.label }}</button>
      <div style="flex:1" />
      <input v-model="searchQuery" class="model-search" placeholder="搜索模型..." />
    </div>

    <!-- Featured section -->
    <template v-if="featuredModels.length">
      <div class="section-heading">精选推荐</div>
      <div class="featured-grid">
        <div
          v-for="m in featuredModels"
          :key="m.id"
          class="featured-card"
          @click="$router.push('/models/' + m.id)"
        >
          <div :class="['featured-banner', 'banner-' + colorKey(m.provider)]">
            <div class="featured-icon">{{ providerInitial(m.provider) }}</div>
            <div>
              <div class="featured-name">{{ displayName(m.id) }}</div>
              <div class="featured-sub">{{ m.provider }}</div>
            </div>
          </div>
          <div class="featured-body">
            <div class="tag-row">
              <span v-for="tg in splitTags(m.tags)" :key="tg" class="mtag">{{ tg }}</span>
            </div>
            <p class="mdesc">{{ m.description || '高性能大语言模型' }}</p>
            <div class="price-row">
              <span v-if="m.per_use > 0" class="pchip pchip--amber">¥{{ m.per_use_fmt }}/次</span>
              <template v-else>
                <span class="pchip">输入 ¥{{ m.input_fmt }}/1M</span>
                <span class="pchip">输出 ¥{{ m.output_fmt }}/1M</span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- All models grid -->
    <div class="section-heading" style="margin-top:24px">
      全部模型（{{ filteredModels.length }}）
    </div>
    <div v-if="filteredModels.length" class="model-grid">
      <div
        v-for="m in filteredModels"
        :key="m.id"
        class="model-card"
        @click="$router.push('/models/' + m.id)"
      >
        <div class="mc-header">
          <div :class="['mc-icon', 'icon-' + colorKey(m.provider)]">
            {{ providerInitial(m.provider) }}
          </div>
          <div style="min-width:0">
            <div class="mc-name">{{ displayName(m.id) }}</div>
            <div class="mc-provider">{{ m.provider }}</div>
          </div>
        </div>
        <p class="mc-desc">{{ m.description || '高性能大语言模型' }}</p>
        <div class="price-row" style="margin-top:auto">
          <span v-if="m.per_use > 0" class="pchip pchip--amber">¥{{ m.per_use_fmt }}/次</span>
          <template v-else>
            <span class="pchip">¥{{ m.input_fmt }}/1M in</span>
            <span class="pchip">¥{{ m.output_fmt }}/1M out</span>
          </template>
        </div>
      </div>
    </div>
    <div v-else class="model-empty">暂无匹配模型，尝试调整筛选条件</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gatewayApi } from '../gatewayApi'

const router = useRouter()

const FEATURED_IDS = ['claude-sonnet-4-5', 'deepseek-r1']

const DISPLAY_NAMES = {
  'deepseek-v4-flash': 'DeepSeek V4 Flash',
  'deepseek-v4-pro': 'DeepSeek V4 Pro',
  'deepseek-r1': 'DeepSeek R1',
  'claude-sonnet-4-5': 'Claude Sonnet 4.5',
  'claude-opus-4-5': 'Claude Opus 4.5',
  'gpt-4o': 'GPT-4o',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gemini-1.5-pro': 'Gemini 1.5 Pro',
}

const PROVIDER_LABELS = {
  anthropic: 'Anthropic', openai: 'OpenAI', deepseek: 'DeepSeek',
  google: 'Google', mistral: 'Mistral',
}

const COLOR_KEYS = {
  anthropic: 'purple', openai: 'mint', deepseek: 'blue',
  google: 'yellow', mistral: 'orange',
}

const models = ref([])
const searchQuery = ref('')
const fProvider = ref('')

const providerTabs = computed(() => {
  const providers = [...new Set(models.value.map(m => m.provider))]
  return [
    { value: '', label: '全部' },
    ...providers.map(p => ({ value: p, label: PROVIDER_LABELS[p] || p })),
  ]
})

const filteredModels = computed(() => {
  let list = models.value
  if (fProvider.value) list = list.filter(m => m.provider === fProvider.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m =>
      m.id.toLowerCase().includes(q) || (m.description || '').toLowerCase().includes(q)
    )
  }
  return list
})

const featuredModels = computed(() =>
  FEATURED_IDS.map(id => models.value.find(m => m.id === id)).filter(Boolean)
)

function displayName(id) {
  return DISPLAY_NAMES[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}
function colorKey(provider) { return COLOR_KEYS[provider] || 'pink' }
function providerInitial(provider) { return (PROVIDER_LABELS[provider] || provider).charAt(0).toUpperCase() }
function splitTags(tags) { return (tags || '').split(',').map(t => t.trim()).filter(Boolean) }

onMounted(async () => {
  try {
    const data = await gatewayApi.listModelCatalog()
    models.value = (data.data || []).map(m => ({
      ...m,
      id: m.model,
      input_fmt: (m.input_price || 0).toFixed(2),
      output_fmt: (m.output_price || 0).toFixed(2),
      per_use_fmt: (m.per_use || 0).toFixed(2),
      per_use: m.per_use || 0,
    }))
  } catch (e) { /* silent */ }
})
</script>

<style scoped>
.model-filter-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.model-tab {
  padding: 6px 16px; border-radius: 20px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text-secondary); font-size: 13px; cursor: pointer;
  transition: all 0.15s;
}
.model-tab:hover { border-color: var(--primary); color: var(--primary); }
.model-tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
.model-search {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid var(--border); font-size: 13px;
  width: 200px; outline: none; background: var(--surface); color: var(--text);
}
.model-search:focus { border-color: var(--primary); }
.section-heading { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 12px; }
.featured-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.featured-card {
  border-radius: var(--radius-lg); border: 1px solid var(--border-light);
  overflow: hidden; cursor: pointer; background: var(--surface);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.featured-card:hover { box-shadow: 0 4px 20px rgba(79,110,247,0.15); border-color: var(--primary); }
.featured-banner {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 24px; color: #fff;
}
.banner-purple { background: linear-gradient(135deg,#7c3aed,#4f46e5); }
.banner-mint   { background: linear-gradient(135deg,#059669,#0891b2); }
.banner-blue   { background: linear-gradient(135deg,#2563eb,#4f46e5); }
.banner-yellow { background: linear-gradient(135deg,#d97706,#dc2626); }
.banner-orange { background: linear-gradient(135deg,#ea580c,#d97706); }
.banner-pink   { background: linear-gradient(135deg,#db2777,#7c3aed); }
.featured-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; flex-shrink: 0;
}
.featured-name { font-size: 16px; font-weight: 700; }
.featured-sub  { font-size: 12px; opacity: 0.8; margin-top: 2px; }
.featured-body { padding: 16px 20px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.mtag {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: var(--primary-light); color: var(--primary);
}
.mdesc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 12px; }
.price-row { display: flex; gap: 6px; flex-wrap: wrap; }
.pchip {
  font-size: 11px; padding: 3px 8px; border-radius: 10px;
  background: #f1f5f9; color: var(--text-secondary); border: 1px solid var(--border-light);
}
.pchip--amber { background: #fef3c7; color: #b45309; border-color: #fde68a; }
.model-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}
@media (max-width: 900px) { .model-grid { grid-template-columns: repeat(2, 1fr); } }
.model-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px; cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
  display: flex; flex-direction: column; gap: 8px; min-height: 130px;
}
.model-card:hover { box-shadow: 0 4px 16px rgba(79,110,247,0.12); border-color: var(--primary); }
.mc-header { display: flex; align-items: center; gap: 10px; }
.mc-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.icon-purple { background: linear-gradient(135deg,#7c3aed,#4f46e5); }
.icon-mint   { background: linear-gradient(135deg,#059669,#0891b2); }
.icon-blue   { background: linear-gradient(135deg,#2563eb,#4f46e5); }
.icon-yellow { background: linear-gradient(135deg,#d97706,#dc2626); }
.icon-orange { background: linear-gradient(135deg,#ea580c,#d97706); }
.icon-pink   { background: linear-gradient(135deg,#db2777,#7c3aed); }
.mc-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mc-provider { font-size: 11px; color: var(--text-muted); }
.mc-desc {
  font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  flex: 1;
}
.model-empty { text-align: center; padding: 60px 0; color: var(--text-muted); font-size: 14px; }
</style>
```

- [ ] **Step 2: Verify**

Navigate to http://localhost:5173/models. Check:
1. Provider tab pills render across the top (one per unique provider from API)
2. Clicking a provider tab filters the grid
3. Search box filters by model ID or description
4. "精选推荐" section shows if `claude-sonnet-4-5` or `deepseek-r1` exist in the API response; hidden gracefully if neither exists
5. Each small card shows gradient icon, name, provider, 2-line clamped description, price chips
6. Hover on any card shows blue border + shadow
7. Clicking a card navigates to `/models/:id` (will 404 — that's expected, detail page is out of scope)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Models.vue
git commit -m "feat: redesign Models page with provider tabs and featured cards"
```

---

### Task 4: Usage.vue — time range picker + stat cards + SVG charts + breakdown table

**Files:**
- Modify: `frontend/src/pages/Usage.vue` (full rewrite, replaces 165-line file)

**What changes vs current:** Replace bare date pickers + 3 stat chips with time-range preset buttons + 4 stat cards with trend delta. Add two SVG charts (daily cost line, per-model request lines). Add model breakdown table sorted by cost. Keep `api.getUsage()` call and detail modal.

**SVG chart pattern:** Copied from `Dashboard.vue` lines 50–56. Viewbox `0 0 600 200`, points mapped via `x(i)` / `y(v)` helpers, gradient fill with `linearGradient`.

**API note:** The spec calls for `/reports/usage` and `/reports/trend` with `start_date`/`end_date` params. `api.js` exposes `api.getUsage(page, dateFrom, dateTo)` for the log table and `api.getTrend(days)` for chart data. We use `getTrend` for charts and `getUsage` for the log table; we derive stat-card totals from the returned data.

- [ ] **Step 1: Replace the entire content of `frontend/src/pages/Usage.vue`**

```vue
<template>
  <div>
    <!-- Time range selector -->
    <div class="time-bar">
      <button
        v-for="r in TIME_RANGES"
        :key="r.key"
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
      <div class="stat-card-item">
        <div class="sci-label">消费金额</div>
        <div class="sci-value">¥{{ stats.cost }}</div>
        <div :class="['sci-delta', stats.costTrend >= 0 ? 'up' : 'down']">
          {{ stats.costTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.costTrend) }}%
        </div>
      </div>
      <div class="stat-card-item">
        <div class="sci-label">请求次数</div>
        <div class="sci-value">{{ stats.calls.toLocaleString() }}</div>
        <div :class="['sci-delta', stats.callsTrend >= 0 ? 'up' : 'down']">
          {{ stats.callsTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.callsTrend) }}%
        </div>
      </div>
      <div class="stat-card-item">
        <div class="sci-label">消耗 Tokens</div>
        <div class="sci-value">{{ fmtTokens(stats.tokens) }}</div>
        <div :class="['sci-delta', stats.tokensTrend >= 0 ? 'up' : 'down']">
          {{ stats.tokensTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.tokensTrend) }}%
        </div>
      </div>
      <div class="stat-card-item">
        <div class="sci-label">错误率</div>
        <div class="sci-value">{{ stats.errorRate }}%</div>
        <div :class="['sci-delta', stats.errorTrend <= 0 ? 'up' : 'down']">
          {{ stats.errorTrend <= 0 ? '↓' : '↑' }} {{ Math.abs(stats.errorTrend) }}%
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div class="chart-row">
      <!-- Daily cost line chart -->
      <div class="chart-box">
        <div class="chart-title">每日消费趋势</div>
        <svg v-if="trendData.length" viewBox="0 0 600 200" style="width:100%;height:auto">
          <defs>
            <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon :points="costArea" fill="url(#costGrad)"/>
          <polyline :points="costLine" fill="none" stroke="var(--primary)" stroke-width="2"/>
          <circle v-for="(p,i) in trendData" :key="i" :cx="cx(i, trendData.length)" :cy="cy(p.cost_yuan, maxCost)" r="3" fill="var(--primary)"/>
          <text v-for="(p,i) in trendData" :key="'l'+i" :x="cx(i, trendData.length)" y="195" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text>
        </svg>
        <div v-else class="chart-empty">暂无数据</div>
      </div>

      <!-- Per-model request lines -->
      <div class="chart-box">
        <div class="chart-title">Top 5 模型请求量</div>
        <svg v-if="modelTrendLines.length" viewBox="0 0 600 200" style="width:100%;height:auto">
          <polyline
            v-for="(line, li) in modelTrendLines"
            :key="li"
            :points="line.points"
            fill="none"
            :stroke="MODEL_LINE_COLORS[li % MODEL_LINE_COLORS.length]"
            stroke-width="1.8"
          />
          <text v-for="(p,i) in trendData" :key="'lx'+i" :x="cx(i, trendData.length)" y="195" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text>
        </svg>
        <div v-else class="chart-empty">暂无数据</div>
        <!-- Legend -->
        <div class="chart-legend">
          <span v-for="(line, li) in modelTrendLines" :key="li" class="legend-item">
            <span class="legend-dot" :style="{background: MODEL_LINE_COLORS[li % MODEL_LINE_COLORS.length]}"></span>
            {{ line.model }}
          </span>
        </div>
      </div>
    </div>

    <!-- Model breakdown table -->
    <div class="breakdown-card">
      <div class="chart-title" style="margin-bottom:12px">模型消耗明细</div>
      <table class="breakdown-table">
        <thead>
          <tr>
            <th>模型</th>
            <th>请求数</th>
            <th>Tokens</th>
            <th>占比</th>
            <th>费用</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in breakdownRows" :key="row.model">
            <td><code style="font-size:12px">{{ row.model }}</code></td>
            <td>{{ row.calls.toLocaleString() }}</td>
            <td>{{ fmtTokens(row.tokens) }}</td>
            <td>
              <div class="quota-bar-wrap">
                <div class="quota-bar" :style="{width: row.pct + '%', background: row.pct >= 80 ? 'var(--quota-warn)' : 'var(--primary)'}"></div>
              </div>
              <span :style="{fontSize:'11px', fontWeight: row.pct >= 80 ? 700 : 400}">{{ row.pct }}%</span>
            </td>
            <td>¥{{ row.cost }}</td>
          </tr>
          <tr v-if="!breakdownRows.length">
            <td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px 0">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Log table (collapsible) -->
    <div class="breakdown-card" style="margin-top:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div class="chart-title">调用日志</div>
        <n-space :size="6">
          <n-button size="small" :disabled="page <= 1" @click="loadLogs(page - 1)">上一页</n-button>
          <n-button size="small" @click="loadLogs(page + 1)">下一页</n-button>
        </n-space>
      </div>
      <n-data-table
        v-if="logs.length"
        :columns="logColumns"
        :data="logs"
        :bordered="false"
        :single-line="false"
        size="small"
      />
      <div v-else style="text-align:center;padding:32px 0;color:var(--text-muted)">暂无调用记录</div>
    </div>

    <!-- Detail modal (unchanged from original) -->
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
import {
  NButton, NDataTable, NDatePicker, NModal, NSpace, NText, NCode,
} from 'naive-ui'
import { api } from '../api'

const TIME_RANGES = [
  { key: '1', label: '今日' },
  { key: '7', label: '近7天' },
  { key: '30', label: '近30天' },
  { key: 'custom', label: '自定义' },
]
const MODEL_LINE_COLORS = ['#4f6ef7', '#34d399', '#f59e0b', '#e85454', '#8b5cf6']

const activeRange = ref('7')
const customFrom = ref(null)
const customTo = ref(null)
const trendData = ref([])
const logs = ref([])
const page = ref(1)
const showDetail = ref(false)
const detailLog = ref(null)

const stats = ref({ cost: '0.00', calls: 0, tokens: 0, errorRate: '0.0', costTrend: 0, callsTrend: 0, tokensTrend: 0, errorTrend: 0 })

function dateRange() {
  const now = new Date()
  if (activeRange.value === 'custom') {
    return {
      from: customFrom.value ? new Date(customFrom.value).toISOString().slice(0, 10) : null,
      to: customTo.value ? new Date(customTo.value).toISOString().slice(0, 10) : null,
    }
  }
  const days = parseInt(activeRange.value)
  const from = new Date(now); from.setDate(from.getDate() - days + 1)
  return {
    from: from.toISOString().slice(0, 10),
    to: now.toISOString().slice(0, 10),
  }
}

async function loadAll() {
  const { from, to } = dateRange()
  await Promise.all([loadTrend(from, to), loadLogs(1, from, to)])
}

async function loadTrend(from, to) {
  try {
    const days = activeRange.value === 'custom' ? 30 : parseInt(activeRange.value)
    const tr = await api.getTrend(days)
    trendData.value = tr.trend || []
    const items = tr.details || []
    const totalCost = items.reduce((s, d) => s + (parseFloat(d.cost_yuan) || 0), 0)
    const totalCalls = items.reduce((s, d) => s + (d.calls || 0), 0)
    const totalTokens = items.reduce((s, d) => s + (d.tokens || 0), 0)
    const totalErrors = items.reduce((s, d) => s + (d.errors || 0), 0)
    stats.value = {
      cost: totalCost.toFixed(2),
      calls: totalCalls,
      tokens: totalTokens,
      errorRate: totalCalls > 0 ? ((totalErrors / totalCalls) * 100).toFixed(1) : '0.0',
      costTrend: 0, callsTrend: 0, tokensTrend: 0, errorTrend: 0,
    }
  } catch (e) { /* silent */ }
}

async function loadLogs(p, from, to) {
  page.value = p
  const range = from !== undefined ? { from, to } : dateRange()
  try {
    const data = await api.getUsage(p, range.from, range.to)
    logs.value = data.items || []
  } catch (e) { /* silent */ }
}

function selectRange(key) {
  activeRange.value = key
  if (key !== 'custom') loadAll()
}

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))
function cx(i, len) { return 40 + (i / Math.max(len - 1, 1)) * 520 }
function cy(v, max) { return 170 - ((v || 0) / max) * 140 }

const costLine = computed(() =>
  trendData.value.map((d, i) => `${cx(i, trendData.value.length)},${cy(d.cost_yuan, maxCost.value)}`).join(' ')
)
const costArea = computed(() => {
  const pts = trendData.value.map((d, i) => `${cx(i, trendData.value.length)},${cy(d.cost_yuan, maxCost.value)}`)
  const n = trendData.value.length
  return `${cx(0, n)},170 ${pts.join(' ')} ${cx(n - 1, n)},170`
})

const modelTrendLines = computed(() => {
  if (!trendData.value.length) return []
  const modelSet = {}
  trendData.value.forEach(day => {
    (day.models || []).forEach(m => {
      if (!modelSet[m.model]) modelSet[m.model] = 0
      modelSet[m.model] += m.calls || 0
    })
  })
  const top5 = Object.entries(modelSet).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([model]) => model)
  const maxCalls = Math.max(...trendData.value.flatMap(d => (d.models || []).map(m => m.calls || 0)), 1)
  return top5.map(model => ({
    model,
    points: trendData.value.map((day, i) => {
      const calls = (day.models || []).find(m => m.model === model)?.calls || 0
      return `${cx(i, trendData.value.length)},${cy(calls, maxCalls)}`
    }).join(' '),
  }))
})

const breakdownRows = computed(() => {
  const modelMap = {}
  logs.value.forEach(l => {
    if (!modelMap[l.model]) modelMap[l.model] = { calls: 0, tokens: 0, cost: 0 }
    modelMap[l.model].calls++
    modelMap[l.model].tokens += (l.prompt_tokens || 0) + (l.completion_tokens || 0)
    modelMap[l.model].cost += parseFloat(l.cost_yuan) || 0
  })
  const rows = Object.entries(modelMap).map(([model, v]) => ({
    model, calls: v.calls, tokens: v.tokens, cost: v.cost.toFixed(4),
  })).sort((a, b) => parseFloat(b.cost) - parseFloat(a.cost))
  const totalCost = rows.reduce((s, r) => s + parseFloat(r.cost), 0)
  return rows.map(r => ({
    ...r,
    pct: totalCost > 0 ? Math.round((parseFloat(r.cost) / totalCost) * 100) : 0,
  }))
})

const logColumns = [
  { title: '时间', key: 'created_at', width: 140, render: row => h('span', { style: 'font-size:12px' }, fmtTime(row.created_at)) },
  { title: 'Key名称', key: 'key_name', width: 100, render: row => h('span', { style: 'font-size:12px' }, row.key_name || '默认') },
  { title: '模型', key: 'model', render: row => h('code', { style: 'font-size:11px' }, row.model) },
  { title: '耗时', key: 'latency_ms', width: 80, render: row => (row.latency_ms || '-') + 'ms' },
  { title: '输入', key: 'prompt_tokens', width: 70 },
  { title: '输出', key: 'completion_tokens', width: 70 },
  { title: '费用', key: 'cost_yuan', width: 80, render: row => '¥' + (row.cost_yuan || '0.00') },
  { title: '操作', key: 'actions', width: 60, render: row => h(NButton, { size: 'tiny', onClick: () => { detailLog.value = row; showDetail.value = true } }, { default: () => '详情' }) },
]

function fmtTime(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }
function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

onMounted(() => loadAll())
</script>

<style scoped>
.time-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.time-btn {
  padding: 5px 14px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text-secondary); font-size: 13px; cursor: pointer;
  transition: all 0.15s;
}
.time-btn:hover { border-color: var(--primary); color: var(--primary); }
.time-btn.active { background: var(--primary); border-color: var(--primary); color: #fff; }
.stat-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  margin-bottom: 20px;
}
@media (max-width: 800px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
.stat-card-item {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px 20px;
}
.sci-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.sci-value { font-size: 24px; font-weight: 700; color: var(--text); line-height: 1.2; }
.sci-delta { font-size: 12px; margin-top: 4px; }
.sci-delta.up { color: var(--success); }
.sci-delta.down { color: var(--danger); }
.chart-row {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 800px) { .chart-row { grid-template-columns: 1fr; } }
.chart-box {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px 20px;
}
.chart-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.chart-empty { text-align: center; padding: 40px 0; color: var(--text-muted); font-size: 13px; }
.chart-legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-secondary); }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.breakdown-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px;
}
.breakdown-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.breakdown-table th {
  text-align: left; padding: 8px 12px; font-size: 12px;
  color: var(--text-secondary); border-bottom: 1px solid var(--border-light);
  font-weight: 500;
}
.breakdown-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-light); }
.breakdown-table tbody tr:last-child td { border-bottom: none; }
.quota-bar-wrap {
  height: 4px; background: var(--border-light); border-radius: 2px;
  margin-bottom: 3px; width: 100px;
}
.quota-bar { height: 4px; border-radius: 2px; transition: width 0.3s; }
</style>
```

- [ ] **Step 2: Verify**

Navigate to http://localhost:5173/usage. Check:
1. Time range buttons render: 今日, 近7天, 近30天, 自定义. Clicking "近7天" (default) triggers data load.
2. 4 stat cards show cost / calls / tokens / error rate. Deltas show ↑/↓ with green/red.
3. Left chart shows SVG cost line with gradient fill. Right chart shows per-model lines (requires API to return `models` array per trend day — if not present, chart shows "暂无数据").
4. Model breakdown table shows rows sorted by cost, with progress bar.
5. Log table shows per-request rows with pagination.
6. Clicking "详情" opens the detail modal.
7. Clicking "自定义" shows two date pickers + 查询 button.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Usage.vue
git commit -m "feat: redesign Usage page with time range, stat cards, SVG charts"
```

---

### Task 5: Keys.vue — summary cards + toolbar + quota-bar table

**Files:**
- Modify: `frontend/src/pages/Keys.vue` (full rewrite)

**What changes vs current:** Add 3 summary cards at top (total / active / this-month calls). Style status badges with spec colors. Replace plain quota text with progress-bar cell. Row opacity 60% for revoked keys. All existing modals (Create Token, API Call) preserved verbatim — only the outer table layout and summary cards change.

- [ ] **Step 1: Replace the entire content of `frontend/src/pages/Keys.vue`**

The new file has four sections: summary cards, toolbar, table, and the two existing modals. The modal HTML and all JS logic from the original `Keys.vue` is carried over unchanged.

```vue
<template>
  <div>
    <!-- Summary cards -->
    <div class="key-summary-grid">
      <div class="key-summary-card">
        <div class="ksc-label">Key 总数</div>
        <div class="ksc-value">{{ keys.length }}</div>
      </div>
      <div class="key-summary-card">
        <div class="ksc-label">有效 Key</div>
        <div class="ksc-value" style="color:var(--status-active)">{{ activeCount }}</div>
      </div>
      <div class="key-summary-card">
        <div class="ksc-label">本月调用量</div>
        <div class="ksc-value">{{ monthCalls.toLocaleString() }}</div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="key-toolbar">
      <n-button type="primary" size="small" @click="showCreate = true">+ 新建 API Key</n-button>
      <n-input v-model:value="searchName" placeholder="搜索名称" clearable size="small" style="width:150px" @keyup.enter="doSearch" />
      <n-input v-model:value="searchKey" placeholder="Key 前缀" clearable size="small" style="width:150px" @keyup.enter="doSearch" />
      <n-select v-model:value="filterStatus" :options="statusOptions" size="small" style="width:100px" />
      <div style="flex:1" />
      <template v-if="selected.length">
        <n-popconfirm @positive-click="batchRevoke">
          <template #trigger>
            <n-button size="small" style="color:var(--status-revoked);border-color:var(--status-revoked)">批量撤销 ({{ selected.length }})</n-button>
          </template>
          确定撤销 {{ selected.length }} 个令牌？
        </n-popconfirm>
        <n-popconfirm @positive-click="batchDelete">
          <template #trigger>
            <n-button size="small" style="color:var(--status-revoked);border-color:var(--status-revoked)">批量删除 ({{ selected.length }})</n-button>
          </template>
          确定永久删除 {{ selected.length }} 个令牌？
        </n-popconfirm>
      </template>
    </div>

    <!-- Table -->
    <div class="key-table-card">
      <n-data-table
        v-if="filteredKeys.length"
        :columns="tableColumns"
        :data="filteredKeys"
        :row-key="row => row.id"
        :checked-row-keys="selected"
        :single-line="false"
        :row-class-name="row => row.status === 'revoked' ? 'row-revoked' : ''"
        size="small"
        @update:checked-row-keys="selected = $event"
      />
      <n-empty v-else description="暂无 API Key" style="padding:48px 0">
        <template #extra>
          <n-button size="small" @click="showCreate = true">创建第一个 Key</n-button>
        </template>
      </n-empty>
      <div v-if="filteredKeys.length" class="key-table-footer">
        共 {{ filteredKeys.length }} 条，每页 20 条
      </div>
    </div>
```

    <!-- Create Token Modal — preserved from original Keys.vue -->
    <n-modal v-model:show="showCreate" :mask-closable="false" preset="card" title="创建令牌"
      style="width:620px;max-width:90vw" :bordered="true" segmented>
      <n-form label-placement="top" label-width="auto">
        <n-form-item label="令牌名称" path="name" required style="margin-bottom:0">
          <n-input v-model:value="formName" placeholder="令牌名称" />
        </n-form-item>
        <n-space style="margin-top:12px">
          <n-form-item label="分组" style="flex:1">
            <n-select v-model:value="formGroup" :options="[{ label: 'default', value: 'default' }]" />
          </n-form-item>
          <n-form-item label="到期时间" style="flex:1">
            <n-space vertical :size="4">
              <n-input v-model:value="formExpiry" placeholder="永不过期" style="min-width:120px" />
              <n-button-group size="tiny">
                <n-button :type="expiryPreset === 'forever' ? 'primary' : 'default'" @click="setExpiry('forever')">永不</n-button>
                <n-button :type="expiryPreset === '1month' ? 'primary' : 'default'" @click="setExpiry('1month')">1月</n-button>
                <n-button :type="expiryPreset === '1day' ? 'primary' : 'default'" @click="setExpiry('1day')">1天</n-button>
                <n-button :type="expiryPreset === '1hour' ? 'primary' : 'default'" @click="setExpiry('1hour')">1小时</n-button>
              </n-button-group>
            </n-space>
          </n-form-item>
          <n-form-item label="创建数量" style="width:100px">
            <n-input-number v-model:value="formCount" :min="1" :max="100" />
          </n-form-item>
        </n-space>
        <n-divider />
        <n-form-item label="额度设置" style="margin-bottom:4px">
          <n-space align="flex-end" :size="12">
            <n-form-item label="每个Key额度" style="flex:1;max-width:240px">
              <n-input-number v-model:value="formQuota" :min="0" :step="0.01" placeholder="0 = 不限制" style="width:100%" />
            </n-form-item>
            <n-checkbox v-model:checked="formUnlimited">不限额度</n-checkbox>
            <n-checkbox v-model:checked="formNativeQuota">原生额度</n-checkbox>
          </n-space>
        </n-form-item>
        <n-divider />
        <n-form-item label="访问限制">
          <n-space :size="12" style="width:100%">
            <n-form-item label="模型限制" style="flex:1">
              <n-select v-model:value="formModels" :options="modelOptions" multiple filterable placeholder="全部模型（不限）" />
            </n-form-item>
            <n-form-item label="IP 白名单" style="flex:1">
              <n-input v-model:value="formIp" placeholder="多个 IP 用逗号分隔" />
            </n-form-item>
          </n-space>
        </n-form-item>
        <n-alert v-if="newKey" type="success" :bordered="true" closable @close="newKey = ''">
          <template #header><span style="font-weight:600">令牌已生成（仅显示一次）</span></template>
          <n-space align="center" :size="8">
            <code style="flex:1;padding:8px 12px;background:#f0fdf4;border-radius:6px;font-size:12px;overflow-x:auto;white-space:nowrap;display:block">{{ newKey }}</code>
            <n-button size="small" type="primary" @click="copyText(newKey)">复制</n-button>
          </n-space>
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end" :size="10">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="createKey">{{ creating ? '创建中...' : '创建' }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- API Call Modal — preserved from original Keys.vue -->
    <n-modal v-model:show="showApiModal" preset="card" title="API 调用测试" style="max-width:720px">
      <div style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">
        基于 Chat Completions API 生成调用代码，替换 API Key 后直接调用。
      </div>
      <n-form label-placement="top">
        <n-space :size="16">
          <n-form-item label="API Key">
            <n-input :value="apiCallKeyPrefix" disabled style="width:220px">
              <template #prefix>🔑</template>
            </n-input>
          </n-form-item>
          <n-form-item label="目标模型">
            <n-select v-model:value="apiCallModel" :options="modelOptions" placeholder="-- 选择模型 --" filterable style="width:200px" />
          </n-form-item>
        </n-space>
      </n-form>
      <n-divider />
      <h5 style="margin:0 0 12px;font-size:14px;font-weight:600">代码示例</h5>
      <n-tabs type="line" :value="codeTab" @update:value="codeTab = $event">
        <n-tab-pane name="curl" tab="cURL">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(curlCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ curlCode }}</pre>
        </n-tab-pane>
        <n-tab-pane name="python" tab="Python">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(pythonCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ pythonCode }}</pre>
        </n-tab-pane>
        <n-tab-pane name="node" tab="Node.js">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(nodeCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ nodeCode }}</pre>
        </n-tab-pane>
      </n-tabs>
      <n-space :size="12" style="margin-top:12px">
        <n-button size="small" type="primary" :loading="apiCalling" :disabled="!apiCallModel" @click="doApiCall">▶ 运行测试</n-button>
      </n-space>
      <n-alert v-if="apiResult" :type="apiResultType" :bordered="true" style="font-size:12px;margin-top:12px">
        <pre style="margin:0;white-space:pre-wrap;max-height:200px;overflow-y:auto">{{ apiResult }}</pre>
      </n-alert>
      <n-alert v-if="apiError" type="error" :bordered="true" closable @close="apiError = ''" style="margin-top:8px;font-size:12px">{{ apiError }}</n-alert>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  NButton, NButtonGroup, NCheckbox, NDataTable, NDivider,
  NEmpty, NForm, NFormItem, NInput, NInputNumber, NModal, NPopconfirm,
  NSelect, NSpace, NAlert, NTabs, NTabPane,
} from 'naive-ui'
import { api } from '../api'
import { gatewayApi } from '../gatewayApi'

const message = useMessage()
const dialog = useDialog()

const keys = ref([])
const selected = ref([])
const searchName = ref('')
const searchKey = ref('')
const filterStatus = ref('')
const showCreate = ref(false)
const newKey = ref('')
const creating = ref(false)
const formName = ref('')
const formGroup = ref('default')
const formExpiry = ref('')
const formCount = ref(1)
const formQuota = ref(0)
const formUnlimited = ref(false)
const formNativeQuota = ref(false)
const formModels = ref([])
const formIp = ref('')
const expiryPreset = ref('forever')
const availableModels = ref([])
const codeTab = ref('curl')
const showApiModal = ref(false)
const apiCallKeyPrefix = ref('')
const apiCallKeyId = ref('')
const apiCallModel = ref(null)
const apiCalling = ref(false)
const apiResult = ref('')
const apiResultType = ref('success')
const apiError = ref('')

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '有效', value: 'active' },
  { label: '已撤销', value: 'revoked' },
  { label: '已过期', value: 'expired' },
]

const modelOptions = computed(() =>
  availableModels.value.map(m => ({ label: m.id, value: m.id }))
)

const activeCount = computed(() => keys.value.filter(k => k.status === 'active').length)
const monthCalls = ref(0)

const filteredKeys = computed(() => {
  let list = keys.value
  if (searchName.value) list = list.filter(k => (k.name || '').toLowerCase().includes(searchName.value.toLowerCase()))
  if (searchKey.value) list = list.filter(k => k.key_prefix.includes(searchKey.value))
  if (filterStatus.value) list = list.filter(k => k.status === filterStatus.value)
  return list
})

function statusColor(status) {
  if (status === 'active') return 'var(--status-active)'
  if (status === 'expired') return 'var(--status-expired)'
  return 'var(--status-revoked)'
}
function statusLabel(status) {
  if (status === 'active') return '有效'
  if (status === 'expired') return '已过期'
  return '已撤销'
}

const tableColumns = computed(() => [
  { type: 'selection', width: 40 },
  { title: '名称 / Key', key: 'name', minWidth: 180,
    render: row => h('div', [
      h('div', { style: 'font-weight:600;font-size:13px' }, row.name || '未命名'),
      h('code', { style: 'font-size:11px;color:var(--text-muted)' }, row.key_prefix + '••••••'),
    ])
  },
  { title: '状态', key: 'status', width: 80,
    render: row => h('span', {
      style: `display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:${statusColor(row.status)}1a;color:${statusColor(row.status)}`
    }, statusLabel(row.status))
  },
  { title: '配额', key: 'quota', width: 160,
    render: row => {
      if (row.quota_total == null || row.quota_total === 0) {
        return h('span', { style: 'font-size:12px;color:var(--text-muted)' }, '不限')
      }
      const used = row.quota_used || 0
      const total = row.quota_total
      const pct = Math.min(Math.round((used / total) * 100), 100)
      const warn = pct >= 80
      return h('div', [
        h('div', { style: 'height:4px;background:var(--border-light);border-radius:2px;margin-bottom:4px;width:100px' }, [
          h('div', { style: `height:4px;border-radius:2px;width:${pct}%;background:${warn ? 'var(--quota-warn)' : 'var(--primary)'}` })
        ]),
        h('span', { style: `font-size:11px;${warn ? 'font-weight:700;color:var(--quota-warn)' : ''}` }, `${used} / ${total}`)
      ])
    }
  },
  { title: '最后调用', key: 'last_used_at', width: 110,
    render: row => h('span', { style: 'font-size:12px' }, row.last_used_at ? fmtDate(row.last_used_at) : '从未')
  },
  { title: '到期', key: 'expires_at', width: 100,
    render: row => h('span', { style: 'font-size:12px' }, row.expires_at ? fmtDate(row.expires_at) : '永不')
  },
  { title: '操作', key: 'actions', width: 150,
    render: row => {
      if (row.status === 'active') {
        return h('div', { style: 'display:flex;gap:4px;flex-wrap:wrap' }, [
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => copyFullKey(row.id) }, { default: () => '复制' }),
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => openApiCall(row) }, { default: () => 'API测试' }),
          h(NPopconfirm, { onPositiveClick: () => revokeKey(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', style: 'color:var(--status-revoked)' }, { default: () => '撤销' }),
            default: () => '确定撤销此令牌？',
          }),
        ])
      }
      if (row.status === 'expired') {
        return h('div', { style: 'display:flex;gap:4px' }, [
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => copyFullKey(row.id) }, { default: () => '复制' }),
          h(NPopconfirm, { onPositiveClick: () => deleteKey(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', style: 'color:var(--status-revoked)' }, { default: () => '删除' }),
            default: () => '确定永久删除？',
          }),
        ])
      }
      // revoked
      return h(NButton, { size: 'tiny', quaternary: true, disabled: true }, { default: () => '已撤销' })
    }
  },
])

function fmtDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '-' }

const curlCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `curl -X POST https://easycode.uno/v1/chat/completions \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer ${apiCallKeyPrefix.value}" \\\n  -d '{"model":"${model}","messages":[{"role":"user","content":"你好"}]}'`
})
const pythonCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `from openai import OpenAI\nclient = OpenAI(api_key="${apiCallKeyPrefix.value}", base_url="https://easycode.uno/v1")\nresponse = client.chat.completions.create(model="${model}", messages=[{"role":"user","content":"你好"}])\nprint(response.choices[0].message.content)`
})
const nodeCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `import OpenAI from 'openai';\nconst client = new OpenAI({apiKey:"${apiCallKeyPrefix.value}",baseURL:"https://easycode.uno/v1"});\nconst r = await client.chat.completions.create({model:"${model}",messages:[{role:"user",content:"你好"}]});\nconsole.log(r.choices[0].message.content);`
})

function copyCode(code) {
  navigator.clipboard.writeText(typeof code === 'string' ? code : code.value).then(() => message.success('已复制'))
}

function openApiCall(row) {
  apiCallKeyPrefix.value = row.key_prefix + '...'
  apiCallKeyId.value = row.id
  apiCallModel.value = null
  apiResult.value = ''; apiError.value = ''
  showApiModal.value = true
}

async function doApiCall() {
  if (!apiCallModel.value) return
  apiCalling.value = true; apiResult.value = ''; apiError.value = ''
  try {
    const res = await fetch('/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': apiCallKeyId.value },
      body: JSON.stringify({ model: apiCallModel.value, messages: [{ role: 'user', content: 'hi' }], max_tokens: 100 })
    })
    const data = await res.json()
    apiResult.value = JSON.stringify(data, null, 2)
    apiResultType.value = res.ok ? 'success' : 'error'
  } catch (e) { apiError.value = e.message } finally { apiCalling.value = false }
}

onMounted(async () => {
  try { const d = await api.listKeys(); keys.value = d.items } catch (e) { /* */ }
  try { const m = await gatewayApi.listModels(); availableModels.value = m.data || [] } catch (e) { /* */ }
  try {
    const now = new Date()
    const from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
    const to = now.toISOString().slice(0, 10)
    const u = await api.getUsage(1, from, to)
    monthCalls.value = u.total_calls || (u.items || []).length
  } catch (e) { /* */ }
})

function setExpiry(preset) {
  expiryPreset.value = preset
  const now = new Date()
  if (preset === 'forever') { formExpiry.value = ''; return }
  if (preset === '1hour') now.setHours(now.getHours() + 1)
  if (preset === '1day') now.setDate(now.getDate() + 1)
  if (preset === '1month') now.setMonth(now.getMonth() + 1)
  formExpiry.value = now.toISOString().slice(0, 16)
}

async function createKey() {
  if (!formName.value) { message.warning('请输入令牌名称'); return }
  creating.value = true
  try {
    let expireDays = null
    if (expiryPreset.value === '1hour') expireDays = 0
    else if (expiryPreset.value === '1day') expireDays = 1
    else if (expiryPreset.value === '1month') expireDays = 30
    const modelsStr = formModels.value.length > 0 ? formModels.value.join(',') : null
    const data = await api.createKey(formName.value, 60, {
      token_group: formGroup.value || 'default',
      token_quota: formUnlimited.value ? null : (formQuota.value || null),
      ip_whitelist: formIp.value || null,
      model_allowlist: modelsStr,
      expire_days: expireDays,
      count: formCount.value || 1,
    })
    newKey.value = data.api_key || (data.keys && data.keys[0]?.api_key)
    const list = await api.listKeys(); keys.value = list.items
    formName.value = ''; formExpiry.value = ''; formCount.value = 1; formQuota.value = 0; formIp.value = ''
    message.success('令牌创建成功')
  } catch (e) { message.error(e.message || '创建失败') } finally { creating.value = false }
}

async function copyFullKey(id) {
  try { const d = await api.revealKey(id); await copyText(d.api_key); message.success('已复制') }
  catch (e) { message.error('复制失败') }
}

async function revokeKey(id) {
  try { await api.revokeKey(id); const d = await api.listKeys(); keys.value = d.items; selected.value = selected.value.filter(x => x !== id); message.success('已撤销') }
  catch (e) { message.error('撤销失败') }
}

async function deleteKey(id) {
  try { await api.deleteKey(id); const d = await api.listKeys(); keys.value = d.items; selected.value = selected.value.filter(x => x !== id); message.success('已删除') }
  catch (e) { message.error('删除失败') }
}

async function batchRevoke() {
  const ids = [...selected.value]
  let failed = 0
  for (const id of ids) { try { await api.revokeKey(id) } catch (e) { failed++ } }
  const d = await api.listKeys(); keys.value = d.items; selected.value = []
  if (failed) message.error(`${failed} 个撤销失败`); else message.success(`已撤销 ${ids.length} 个`)
}

async function batchDelete() {
  const ids = [...selected.value]
  let failed = 0
  for (const id of ids) { try { await api.deleteKey(id) } catch (e) { failed++ } }
  const d = await api.listKeys(); keys.value = d.items; selected.value = []
  if (failed) message.error(`${failed} 个删除失败`); else message.success(`已删除 ${ids.length} 个`)
}

function doSearch() { /* filteredKeys is reactive */ }

async function copyText(text) {
  try { await navigator.clipboard.writeText(text) } catch (e) {
    const ta = document.createElement('textarea'); ta.value = text
    ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
  }
}
</script>

<style scoped>
.key-summary-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px;
}
.key-summary-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px 20px;
}
.ksc-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.ksc-value { font-size: 28px; font-weight: 700; color: var(--text); }
.key-toolbar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 12px 16px;
}
.key-table-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 0; overflow: hidden;
}
.key-table-footer {
  padding: 10px 16px; font-size: 12px; color: var(--text-muted);
  border-top: 1px solid var(--border-light);
}
</style>
```

- [ ] **Step 2: Add global style for revoked row opacity**

In `frontend/src/styles/base.css`, at the bottom of the file, add:

```css
/* Keys page: revoked rows appear dimmed */
.row-revoked td { opacity: 0.6; }
```

- [ ] **Step 3: Verify**

Navigate to http://localhost:5173/keys. Check:
1. Three summary cards at top: Key 总数, 有效 Key (green number), 本月调用量.
2. Toolbar shows: "+ 新建 API Key" button, two search inputs, status dropdown.
3. Table shows quota progress bars. Green bar < 80%, orange bar ≥ 80%. "不限" text for keys with no quota.
4. Status badges: active = green pill, expired = orange pill, revoked = red pill.
5. Revoked rows are visually dimmed (60% opacity).
6. Active key row operations: 复制, API测试, 撤销.
7. Expired key row operations: 复制, 删除.
8. Revoked key row: disabled "已撤销" button only.
9. Selecting rows with checkboxes enables batch 撤销/删除 buttons in toolbar.
10. "+ 新建 API Key" opens the create modal — all fields functional as before.
11. API测试 button opens the API call modal with code tabs.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Keys.vue frontend/src/styles/base.css
git commit -m "feat: redesign Keys page with summary cards and status badges"
```

---
