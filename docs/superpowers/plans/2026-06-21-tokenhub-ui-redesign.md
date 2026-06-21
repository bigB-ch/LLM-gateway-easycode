# TokenHub 风格 UI 重设计实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 LLM Gateway 用户端三个核心页面（模型广场、用量监控、API Key 管理）重设计为 TokenHub 风格，保留所有现有业务逻辑。

**Architecture:** 每个页面独立重写，保持现有 API 调用逻辑不变，仅替换模板结构和样式。复用 base.css 已有的 CSS 变量和组件类，不引入新依赖。

**Tech Stack:** Vue 3 Composition API, Naive UI 2.44, Vite, 现有 api.js / gatewayApi.js

---

## Task 1: UserLayout.vue — 侧边栏导航顺序调整

**文件:** `frontend/src/layouts/UserLayout.vue`

**目标:** 将导航菜单重排为 TokenHub 规范顺序：仪表盘 / 模型广场 / 用量监控 / API Key / Playground / 充值 / 设置。合并两个 sidebar-section 分组为单一"控制台"分组，消除视觉割裂。

### Steps

- [ ] **1.1 完整替换 `<template>` 块**（原第 1–31 行）

  ```vue
  <template>
    <div class="app-shell">
      <TopNavBar />
      <div class="app-body">
        <aside :class="'sidebar ' + (collapsed ? 'collapsed' : '')">
          <div class="sidebar-section">控制台</div>
          <nav class="sidebar-nav">
            <router-link to="/"><span class="nav-icon">&#x25A3;</span> <span>{{ t('dashboard') }}</span></router-link>
            <router-link to="/models"><span class="nav-icon">&#x1F310;</span> <span>{{ t('marketplace') }}</span></router-link>
            <router-link to="/usage"><span class="nav-icon">&#x1F4C4;</span> <span>{{ t('usage') }}</span></router-link>
            <router-link to="/keys"><span class="nav-icon">&#x1F511;</span> <span>{{ t('tokens') }}</span></router-link>
            <router-link to="/playground"><span class="nav-icon">&#x1F4AC;</span> <span>{{ t('playground') }}</span></router-link>
            <router-link to="/plans"><span class="nav-icon">&#x1F4B0;</span> <span>{{ t('wallet') }}</span></router-link>
            <router-link to="/settings"><span class="nav-icon">&#x2699;&#xFE0F;</span> <span>{{ t('settings') }}</span></router-link>
          </nav>
          <div class="sidebar-collapse-btn" @click="collapsed = !collapsed">
            <span class="collapse-icon">&#x00AB;</span>
            <span class="sidebar-collapse-text">{{ t('collapse') }}</span>
          </div>
        </aside>
        <main class="page-main">
          <router-view />
        </main>
      </div>
    </div>
  </template>
  ```

- [ ] **1.2 `<script setup>` 保持不变** — 无需修改，保留原有 `collapsed` ref 和 `useI18n` 导入。

- [ ] **1.3 验证**

  ```bash
  cd D:/code/llm-gateway/frontend && npm run dev
  ```

  打开 http://localhost:5173，检查左侧导航顺序：仪表盘 → 模型广场 → 用量监控 → API Key → Playground → 充值 → 设置。确认收起/展开按钮正常，active 高亮（左侧蓝色竖条 + 浅蓝背景）随路由切换正常。

- [ ] **1.4 提交**

  ```bash
  cd D:/code/llm-gateway
  git add frontend/src/layouts/UserLayout.vue
  git commit -m "feat: reorder sidebar nav to TokenHub spec order"
  ```

---

## Task 2: Models.vue — 模型广场重写

**文件:** `frontend/src/pages/Models.vue`

**目标:** 用 TokenHub 风格的供应商 chip 过滤栏 + 精选 2 列大卡片 + 3 列小卡片网格，替换现有左侧面板 + 网格/表格布局。保留全部 `<script setup>` 逻辑不变。

### 背景

现有 script 中保留所有变量和函数：`models`, `searchQuery`, `fProvider`, `fTag`, `fBilling`, `filteredModels`, `providerOptions`, `tagOptions`, `MODEL_DISPLAY`, `PROVIDER_NAMES`, `MODEL_COLORS`, `copyModelId()`, `modelDisplayName()`, `providerName()`, `modelColor()`, `resetFilters()`，以及 `onMounted` 中的 `gatewayApi.listModelCatalog()` 调用。全部保留，不删除任何现有逻辑。

### Steps

- [ ] **2.1 在 `<script setup>` 顶部追加新常量**（插入位置：`const models = ref([])` 之前）

  ```js
  const FEATURED_MODEL_IDS = ['claude-sonnet-4-5', 'deepseek-r1']

  const PROVIDER_CHIPS = [
    { value: '', label: '全部' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'google', label: 'Google' },
  ]

  const PROVIDER_GRADIENTS = {
    anthropic: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)',
    openai:    'linear-gradient(135deg, #059669 0%, #34d399 100%)',
    deepseek:  'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
    google:    'linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)',
    default:   'linear-gradient(135deg, var(--primary) 0%, #7c3aed 100%)',
  }
  ```

- [ ] **2.2 在 `filteredModels` computed 之后追加两个新 computed**

  ```js
  const featuredModels = computed(() =>
    FEATURED_MODEL_IDS
      .map(id => filteredModels.value.find(m => m.id === id))
      .filter(Boolean)
  )

  const gridModels = computed(() =>
    filteredModels.value.filter(m => !FEATURED_MODEL_IDS.includes(m.id))
  )
  ```

- [ ] **2.3 在 `resetFilters()` 之后追加辅助函数**

  ```js
  function providerGradient(provider) {
    return PROVIDER_GRADIENTS[provider] || PROVIDER_GRADIENTS.default
  }
  ```

- [ ] **2.4 完整替换 `<template>` 块**（原第 1–110 行）

  ```vue
  <template>
    <div>
      <!-- 过滤栏：供应商 chips + 搜索框 -->
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:20px">
        <span
          v-for="chip in PROVIDER_CHIPS"
          :key="chip.value"
          :style="{
            display:'inline-flex', alignItems:'center', padding:'5px 14px',
            borderRadius:'999px', fontSize:'13px', fontWeight:'500', cursor:'pointer',
            border: fProvider === chip.value ? '1px solid var(--primary)' : '1px solid var(--border)',
            background: fProvider === chip.value ? 'var(--primary-light)' : 'var(--surface)',
            color: fProvider === chip.value ? 'var(--primary)' : 'var(--text-secondary)',
            transition: 'all 0.12s',
          }"
          @click="fProvider = chip.value"
        >{{ chip.label }}</span>
        <div style="flex:1;min-width:160px;max-width:260px;margin-left:auto">
          <n-input v-model:value="searchQuery" placeholder="搜索模型名称..." size="small" clearable />
        </div>
      </div>

      <!-- 精选推荐（2 列大卡） -->
      <template v-if="featuredModels.length">
        <div style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px">精选推荐</div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px">
          <div
            v-for="m in featuredModels"
            :key="m.id"
            class="card"
            style="overflow:hidden;cursor:pointer;transition:box-shadow 0.15s,border-color 0.15s"
            @click="$router.push('/models/' + m.id)"
            @mouseenter="e => { e.currentTarget.style.boxShadow='0 4px 20px rgba(79,110,247,0.15)'; e.currentTarget.style.borderColor='var(--primary)' }"
            @mouseleave="e => { e.currentTarget.style.boxShadow=''; e.currentTarget.style.borderColor='' }"
          >
            <div :style="{
              background: providerGradient(m.provider),
              padding: '20px 24px', color: '#fff', position: 'relative', overflow: 'hidden'
            }">
              <div style="position:absolute;top:-20px;right:-20px;width:100px;height:100px;border-radius:50%;background:rgba(255,255,255,0.08)"></div>
              <div style="font-size:18px;font-weight:700;position:relative">{{ modelDisplayName(m.id) }}</div>
              <div style="font-size:12px;opacity:0.8;margin-top:4px;position:relative">{{ providerName(m.provider) }}</div>
            </div>
            <div style="padding:16px 20px">
              <div v-if="m.tags" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px">
                <span v-for="tg in m.tags.split(',').slice(0,4)" :key="tg" class="badge badge-primary" style="font-size:11px">{{ tg.trim() }}</span>
              </div>
              <div v-if="m.description" style="font-size:13px;color:var(--text-secondary);line-height:1.5;margin-bottom:12px">{{ m.description }}</div>
              <div style="display:flex;gap:16px;font-size:12px;color:var(--text-muted)">
                <span v-if="m.per_use === 0">输入 <b style="color:var(--text)">¥{{ m.input_fmt }}/1M</b></span>
                <span v-if="m.per_use === 0">输出 <b style="color:var(--text)">¥{{ m.output_fmt }}/1M</b></span>
                <span v-if="m.per_use > 0">按次计费 <b style="color:#d97706">¥{{ m.per_use_fmt }}/次</b></span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 全部模型（3 列小卡网格） -->
      <div style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px">
        全部模型 <span style="font-size:13px;font-weight:400;color:var(--text-muted);margin-left:6px">{{ filteredModels.length }} 个</span>
      </div>
      <div v-if="gridModels.length" style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
        <div
          v-for="m in gridModels"
          :key="m.id"
          class="card"
          style="padding:16px;cursor:pointer;transition:box-shadow 0.15s,border-color 0.15s;display:flex;flex-direction:column;gap:10px"
          @click="$router.push('/models/' + m.id)"
          @mouseenter="e => { e.currentTarget.style.boxShadow='0 4px 16px rgba(79,110,247,0.12)'; e.currentTarget.style.borderColor='var(--primary)' }"
          @mouseleave="e => { e.currentTarget.style.boxShadow=''; e.currentTarget.style.borderColor='' }"
        >
          <div style="display:flex;align-items:center;gap:10px">
            <div :style="{
              width:'36px', height:'36px', borderRadius:'8px', flexShrink:0,
              background:providerGradient(m.provider),
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:'15px', color:'#fff', fontWeight:'700',
            }">
              {{ (modelDisplayName(m.id)[0] || '?').toUpperCase() }}
            </div>
            <div style="min-width:0">
              <div style="font-size:13px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ modelDisplayName(m.id) }}</div>
              <div style="font-size:11px;color:var(--text-muted)">{{ providerName(m.provider) }}</div>
            </div>
          </div>
          <div v-if="m.description" style="font-size:12px;color:var(--text-secondary);line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ m.description }}</div>
          <div style="margin-top:auto;display:flex;gap:6px;flex-wrap:wrap">
            <span v-if="m.per_use === 0" class="badge badge-default" style="font-size:11px">¥{{ m.input_fmt }}/1M in</span>
            <span v-if="m.per_use === 0" class="badge badge-default" style="font-size:11px">¥{{ m.output_fmt }}/1M out</span>
            <span v-if="m.per_use > 0" class="badge badge-warning" style="font-size:11px">¥{{ m.per_use_fmt }}/次</span>
          </div>
        </div>
      </div>
      <div v-else-if="!filteredModels.length" class="card card-padded" style="text-align:center;padding:48px 24px">
        <div style="font-size:32px;opacity:0.3;margin-bottom:12px">&#x1F310;</div>
        <div style="color:var(--text-muted);font-size:14px">暂无匹配模型，尝试调整筛选条件</div>
      </div>
    </div>
  </template>
  ```

- [ ] **2.5 替换 `<style scoped>` 块**

  ```vue
  <style scoped>
  /* model-grid replaced by inline grid styles */
  </style>
  ```

- [ ] **2.6 验证**

  ```bash
  cd D:/code/llm-gateway/frontend && npm run dev
  ```

  打开 http://localhost:5173/models，检查：顶部 chip 栏过滤正常；精选大卡（若有数据）2 列渐变 banner；3 列小卡悬停蓝色边框；点击跳转 `/models/:id` 无 JS 错误。

- [ ] **2.7 提交**

  ```bash
  cd D:/code/llm-gateway
  git add frontend/src/pages/Models.vue
  git commit -m "feat: redesign Models page to TokenHub style with featured cards and chip filter"
  ```

---

## Task 3: Usage.vue — 用量监控重写

**文件:** `frontend/src/pages/Usage.vue`

**目标:** 新增时间预设按钮、4 格统计卡、2 列 SVG 折线图、模型消耗明细表，替换现有简陋布局。保留 `api.getUsage()`、`loadPage()`、`logs` ref、detail modal 全部逻辑。

### 背景

现有 script 保留全部变量和函数：`logs`, `page`, `detailLog`, `showDetail`, `dateFromTs`, `dateToTs`, `filterKeyName`, `filterModel`, `filterGroup`, `filterReqId`, `filterStatus`, `totalCost`, `rpm`, `tpm`, `filteredLogs`, `tableColumns`, `loadPage()`, `doSearch()`, `resetFilter()`, `fmtTime()`。新增内容均追加在末尾，不修改已有代码。

### Steps

- [ ] **3.1 修改 vue import 行**，补充 `watch`：

  将 `import { ref, computed, h, onMounted } from 'vue'` 改为：

  ```js
  import { ref, computed, h, onMounted, watch } from 'vue'
  ```

- [ ] **3.2 在 `fmtTime()` 函数之后追加新状态和逻辑**

  ```js
  // ── 时间预设 ──
  const timePreset = ref('7d')

  function applyPreset(preset) {
    timePreset.value = preset
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    if (preset === 'today') {
      dateFromTs.value = today.getTime()
      dateToTs.value = today.getTime()
    } else if (preset === 'yesterday') {
      const y = new Date(today); y.setDate(y.getDate() - 1)
      dateFromTs.value = y.getTime(); dateToTs.value = y.getTime()
    } else if (preset === '7d') {
      const d = new Date(today); d.setDate(d.getDate() - 6)
      dateFromTs.value = d.getTime(); dateToTs.value = today.getTime()
    } else if (preset === '30d') {
      const d = new Date(today); d.setDate(d.getDate() - 29)
      dateFromTs.value = d.getTime(); dateToTs.value = today.getTime()
    }
    loadPage(1)
  }

  // ── 趋势图数据 ──
  const trendDays = ref([])
  const modelTrend = ref([])

  async function loadTrend() {
    try {
      const days = timePreset.value === '30d' ? 30 : 7
      const data = await api.getTrend(days)
      trendDays.value = (data.days || []).map(d => ({
        date: d.date,
        cost: parseFloat(d.cost_yuan || 0),
        requests: d.requests || 0,
      }))
      const byModel = {}
      ;(data.model_breakdown || []).forEach(row => {
        if (!byModel[row.model]) byModel[row.model] = []
        byModel[row.model].push({ date: row.date, requests: row.requests || 0 })
      })
      modelTrend.value = Object.entries(byModel)
        .map(([model, pts]) => ({ model, pts, total: pts.reduce((s,p) => s+p.requests, 0) }))
        .sort((a,b) => b.total - a.total).slice(0,5)
        .map(({ model, pts }) => ({ model, points: pts }))
    } catch(e) { /* silent */ }
  }

  // ── 统计卡数据 ──
  const statCards = ref([
    { label: '消费额', value: '¥0.00', icon: '&#x1F4B0;', color: 'mc-blue' },
    { label: '请求数', value: '0', icon: '&#x1F4CA;', color: 'mc-purple' },
    { label: '总 Tokens', value: '0', icon: '&#x26A1;', color: 'mc-mint' },
    { label: '错误率', value: '0%', icon: '&#x26A0;', color: 'mc-orange' },
  ])
  const modelBreakdown = ref([])

  function buildStats() {
    const list = logs.value
    if (!list.length) return
    const totalReq = list.length
    const totalTok = list.reduce((s,l) => s+(l.prompt_tokens||0)+(l.completion_tokens||0), 0)
    const totalErr = list.filter(l => l.status === 'error').length
    const errRate = totalReq ? ((totalErr/totalReq)*100).toFixed(1) : '0.0'
    statCards.value[0].value = '¥' + (parseFloat(totalCost.value)||0).toFixed(2)
    statCards.value[1].value = totalReq.toLocaleString()
    statCards.value[2].value = totalTok >= 1e6 ? (totalTok/1e6).toFixed(2)+'M'
      : totalTok >= 1000 ? (totalTok/1000).toFixed(1)+'K' : String(totalTok)
    statCards.value[3].value = errRate + '%'
    const byModel = {}
    list.forEach(l => {
      const m = l.model || 'unknown'
      if (!byModel[m]) byModel[m] = { requests:0, tokens:0, cost:0 }
      byModel[m].requests++
      byModel[m].tokens += (l.prompt_tokens||0)+(l.completion_tokens||0)
      byModel[m].cost += parseFloat(l.cost_yuan||0)
    })
    const tc = parseFloat(totalCost.value)||1
    modelBreakdown.value = Object.entries(byModel)
      .map(([model,d]) => ({
        model, requests:d.requests, tokens:d.tokens,
        cost:d.cost.toFixed(4), pct:Math.round((d.cost/tc)*100),
      }))
      .sort((a,b) => parseFloat(b.cost)-parseFloat(a.cost))
  }

  // ── SVG 折线图辅助（复用 Dashboard.vue 模式，viewBox 0 0 600 200）──
  function svgX(i, n) { return n<=1 ? 300 : Math.round(20+(i/(n-1))*560) }
  function svgY(v, min, max) { return max===min ? 100 : Math.round(180-((v-min)/(max-min))*160) }
  function linePath(ys) {
    const n=ys.length; if(!n) return ""
    return ys.map((y,i) => (i===0?"M":"L")+svgX(i,n)+","+y).join(" ")
  }
  function areaPath(ys) {
    const n=ys.length; if(!n) return ""
    const line=ys.map((y,i)=>svgX(i,n)+","+y).join(" L ")
    return "M "+svgX(0,n)+","+ys[0]+" L "+line+" L "+svgX(n-1,n)+",180 L "+svgX(0,n)+",180 Z"
  }
  const LINE_COLORS = ['var(--primary)','#34d399','#f59e0b','#ec4899','#8b5cf6']

  const costChart = computed(() => {
    const vals = trendDays.value.map(d=>d.cost)
    if(!vals.length) return { line:'', area:'' }
    const max=Math.max(...vals)||1
    const ys=vals.map(v=>svgY(v,0,max))
    return { line:linePath(ys), area:areaPath(ys) }
  })

  const modelLines = computed(() => {
    if(!modelTrend.value.length) return []
    const allDates=[...new Set(modelTrend.value.flatMap(m=>m.points.map(p=>p.date)))].sort()
    const maxReq=Math.max(...modelTrend.value.flatMap(m=>m.points.map(p=>p.requests)))||1
    return modelTrend.value.map((m,idx) => {
      const map=Object.fromEntries(m.points.map(p=>[p.date,p.requests]))
      const ys=allDates.map(d=>svgY(map[d]||0,0,maxReq))
      return { model:m.model, path:linePath(ys), color:LINE_COLORS[idx%5] }
    })
  })

  const dateLabels = computed(() => {
    const n=trendDays.value.length
    return trendDays.value.map((d,i)=>({ x:svgX(i,n), label:d.date.slice(5) }))
  })

  onMounted(() => { applyPreset("7d"); loadTrend() })
  watch(logs, buildStats)
  ```

- [ ] **3.3 完整替换 `<template>` 块**（原第 1–76 行）

  ```vue
  <template>
    <div>
      <!-- 时间预设栏 -->
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:20px;flex-wrap:wrap">
        <span style="font-size:13px;color:var(--text-secondary);margin-right:4px">时间范围：</span>
        <button v-for="p in [{v:'today',l:'今日'},{v:'yesterday',l:'昨日'},{v:'7d',l:'近7天'},{v:'30d',l:'近30天'}]"
          :key="p.v"
          :class="['btn','btn-sm', timePreset===p.v ? 'btn-primary' : 'btn-outline']"
          @click="applyPreset(p.v)">{{ p.l }}</button>
        <div style="display:flex;align-items:center;gap:6px;margin-left:8px">
          <n-date-picker v-model:value="dateFromTs" type="date" placeholder="开始" size="small" style="width:120px" />
          <span style="color:var(--text-muted)">~</span>
          <n-date-picker v-model:value="dateToTs" type="date" placeholder="结束" size="small" style="width:120px" />
          <button class="btn btn-sm btn-primary" @click="() => { timePreset='custom'; loadPage(1); loadTrend() }">查询</button>
        </div>
      </div>

      <!-- 4 格统计卡 -->
      <div class="stat-grid" style="margin-bottom:20px">
        <div v-for="card in statCards" :key="card.label" :class="['stat-card', card.color]">
          <div class="stat-icon" v-html="card.icon"></div>
          <div class="stat-body">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </div>

      <!-- 2 列趋势图 -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
        <div class="card card-padded">
          <div style="font-size:14px;font-weight:600;margin-bottom:12px">每日消费趋势</div>
          <div class="chart-wrap">
            <svg viewBox="0 0 600 200" preserveAspectRatio="none">
              <defs>
                <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.25"/>
                  <stop offset="100%" stop-color="var(--primary)" stop-opacity="0.02"/>
                </linearGradient>
              </defs>
              <path v-if="costChart.area" :d="costChart.area" fill="url(#costGrad)" />
              <path v-if="costChart.line" :d="costChart.line" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linejoin="round" />
              <text v-for="(item,i) in dateLabels" :key="i" :x="item.x" y="198" text-anchor="middle" font-size="10" fill="#aaa">{{ item.label }}</text>
              <text v-if="!costChart.line" x="300" y="100" text-anchor="middle" font-size="13" fill="#ccc">暂无数据</text>
            </svg>
          </div>
        </div>
        <div class="card card-padded">
          <div style="font-size:14px;font-weight:600;margin-bottom:12px">模型请求量（Top 5）</div>
          <div class="chart-wrap">
            <svg viewBox="0 0 600 200" preserveAspectRatio="none">
              <path v-for="(ml,idx) in modelLines" :key="idx" :d="ml.path" fill="none" :stroke="ml.color" stroke-width="2" stroke-linejoin="round" />
              <g v-for="(ml,idx) in modelLines" :key="'leg'+idx" :transform="`translate(20,${16+idx*16})`">
                <line x1="0" y1="6" x2="16" y2="6" :stroke="ml.color" stroke-width="2"/>
                <text x="20" y="10" font-size="10" :fill="ml.color">{{ ml.model }}</text>
              </g>
              <text v-if="!modelLines.length" x="300" y="100" text-anchor="middle" font-size="13" fill="#ccc">暂无数据</text>
            </svg>
          </div>
        </div>
      </div>

      <!-- 模型消耗明细表 -->
      <div class="card" style="margin-bottom:20px">
        <div style="padding:16px 20px;border-bottom:1px solid var(--border-light);font-size:14px;font-weight:600">模型消耗明细</div>
        <table class="data-table" style="width:100%">
          <thead><tr><th>模型</th><th>请求数</th><th>Tokens</th><th style="width:200px">消费占比</th><th>费用</th></tr></thead>
          <tbody>
            <tr v-for="row in modelBreakdown" :key="row.model">
              <td><code style="font-size:12px;font-family:var(--font-mono)">{{ row.model }}</code></td>
              <td>{{ row.requests.toLocaleString() }}</td>
              <td>{{ row.tokens.toLocaleString() }}</td>
              <td>
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="flex:1;height:6px;background:var(--border-light);border-radius:3px;overflow:hidden">
                    <div :style="{ height:'100%', width:row.pct+'%', background:row.pct>=80?'#f59e0b':'var(--primary)', borderRadius:'3px', transition:'width 0.3s' }"></div>
                  </div>
                  <span style="font-size:12px;color:var(--text-secondary);width:36px;text-align:right">{{ row.pct }}%</span>
                </div>
              </td>
              <td style="font-weight:600">¥{{ row.cost }}</td>
            </tr>
            <tr v-if="!modelBreakdown.length"><td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px">暂无数据</td></tr>
          </tbody>
        </table>
      </div>

      <!-- 调用明细日志表 -->
      <div class="card">
        <div style="padding:16px 20px;border-bottom:1px solid var(--border-light);display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:14px;font-weight:600">调用明细</span>
          <div style="display:flex;gap:8px">
            <n-input v-model:value="filterModel" placeholder="模型名" size="small" style="width:110px" />
            <n-select v-model:value="filterStatus" :options="[{label:'全部',value:''},{label:'成功',value:'success'},{label:'失败',value:'error'}]" size="small" style="width:80px" />
            <button class="btn btn-sm btn-primary" @click="doSearch">查询</button>
            <button class="btn btn-sm btn-outline" @click="resetFilter">重置</button>
          </div>
        </div>
        <n-data-table v-if="filteredLogs.length" :columns="tableColumns" :data="filteredLogs" :bordered="false" :single-line="false" :min-height="100" />
        <div v-else style="text-align:center;padding:32px;color:var(--text-muted);font-size:13px">暂无调用记录</div>
        <div style="padding:12px 20px;display:flex;justify-content:center;gap:8px;border-top:1px solid var(--border-light)">
          <button class="btn btn-sm btn-outline" :disabled="page<=1" @click="loadPage(1)">上一页</button>
          <button class="btn btn-sm btn-outline" @click="loadPage(page+1)">下一页</button>
        </div>
      </div>

      <!-- 调用详情 Modal（原有，保留） -->
      <n-modal v-model:show="showDetail" preset="card" title="调用详情" style="max-width:480px" :bordered="true">
        <n-space vertical :size="8">
          <n-text depth="2" style="font-size:12px">Request ID: <n-code>{{ detailLog?.id }}</n-code></n-text>
          <n-text depth="2" style="font-size:12px">模型: {{ detailLog?.model }}</n-text>
          <n-text depth="2" style="font-size:12px">时间: {{ fmtTime(detailLog?.created_at) }}</n-text>
          <n-text depth="2" style="font-size:12px">耗时: {{ detailLog?.duration_ms || '-' }}ms</n-text>
          <n-text depth="2" style="font-size:12px">Tokens: {{ detailLog?.prompt_tokens }} in / {{ detailLog?.completion_tokens }} out</n-text>
          <n-text depth="2" style="font-size:12px">花费: ¥{{ detailLog?.cost_yuan || '0.00' }}</n-text>
          <n-text depth="2" style="font-size:12px">IP: {{ detailLog?.ip || '-' }}</n-text>
        </n-space>
      </n-modal>
    </div>
  </template>
  ```

- [ ] **3.4 验证**

  ```bash
  cd D:/code/llm-gateway/frontend && npm run dev
  ```

  打开 http://localhost:5173/usage，检查：时间预设按钮激活高亮；4 格统计卡数据正确；消费趋势折线含渐变填充；模型多线图有图例；明细表进度条 ≥80% 变橙；调用明细表和 Modal 正常。

- [ ] **3.5 提交**

  ```bash
  cd D:/code/llm-gateway
  git add frontend/src/pages/Usage.vue
  git commit -m "feat: redesign Usage page with stat cards, SVG charts and model breakdown"
  ```

---

## Task 4: Keys.vue — API Key 管理重写

**文件:** `frontend/src/pages/Keys.vue`

**目标:** 新增 3 格汇总卡 + 工具栏（搜索/状态筛选/分组筛选/批量操作）；用 `.badge-success`/`.badge-danger`/`.badge-warning` 替换 NTag 状态徽章；配额列改为内联进度条；已撤销行整行 60% 透明；新建按钮移至页面顶栏右侧。保留全部现有 script 逻辑。

### 背景

现有 script 保留全部变量和函数：`keys`, `showCreate`, `newKey`, `creating`, `formName`, `formGroup`, `formExpiry`, `formCount`, `formQuota`, `formUnlimited`, `formNativeQuota`, `formModels`, `formIp`, `expiryPreset`, `selected`, `searchName`, `searchKey`, `filteredKeys`, `allSelected`, `tableColumns`, `createKey()`, `copyFullKey()`, `revokeKey()`, `deleteKey()`, `batchRevoke()`, `batchDelete()`, `copyText()`, `setExpiry()`，以及 API Call Modal 相关所有变量。新增内容追加在 `filteredKeys` computed 之后。

### Steps

- [ ] **4.1 在 `filteredKeys` computed 之后追加新状态**

  ```js
  const filterStatusBar = ref('')
  const filterGroupBar = ref('')

  const summaryCards = computed(() => {
    const all = keys.value
    const active = all.filter(k => k.status === 'active').length
    const thisMonthCalls = all.reduce((s,k) => s+(k.calls_this_month||0), 0)
    return [
      { label: 'Key 总数', value: all.length, icon: '&#x1F511;', color: 'mc-blue' },
      { label: '有效 Key', value: active, icon: '&#x2705;', color: 'mc-mint' },
      { label: '本月调用', value: thisMonthCalls.toLocaleString(), icon: '&#x1F4CA;', color: 'mc-purple' },
    ]
  })

  const filteredKeysBar = computed(() => {
    let list = filteredKeys.value
    if (filterStatusBar.value) list = list.filter(k => k.status === filterStatusBar.value)
    if (filterGroupBar.value) list = list.filter(k => (k.group||"default") === filterGroupBar.value)
    return list
  })

  const groupOptions = computed(() => {
    const groups = [...new Set(keys.value.map(k => k.group||'default'))]
    return [{ label: '全部分组', value: '' }, ...groups.map(g => ({ label:g, value:g }))]
  })
  ```

- [ ] **4.2 完整替换 `<template>` 块**（原第 1–234 行；全部两个 `<n-modal>` 块完整保留）

  ```vue
  <template>
    <div>
      <!-- 顶栏：标题 + 新建按钮 -->
      <div class="flex-between mb-16">
        <h1 class="page-title">API Key 管理</h1>
        <button class="btn btn-primary btn-sm" @click="showCreate = true">+ 新建 API Key</button>
      </div>

      <!-- 3 格汇总卡 -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px">
        <div v-for="card in summaryCards" :key="card.label" :class="['stat-card', card.color]">
          <div class="stat-icon" v-html="card.icon"></div>
          <div class="stat-body">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </div>

      <!-- 工具栏 -->
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px">
        <n-input v-model:value="searchName" placeholder="搜索 Key 名称" clearable size="small" style="width:160px" @keyup.enter="doSearch" />
        <n-select v-model:value="filterStatusBar" :options="[{label:'全部状态',value:''},{label:'有效',value:'active'},{label:'已撤销',value:'revoked'},{label:'已过期',value:'expired'}]" size="small" style="width:110px" />
        <n-select v-model:value="filterGroupBar" :options="groupOptions" size="small" style="width:110px" />
        <div style="flex:1" />
        <n-popconfirm v-if="selected.length" @positive-click="batchRevoke">
          <template #trigger>
            <button class="btn btn-sm btn-outline" style="color:#dc2626;border-color:#dc2626">吊销所选 ({{ selected.length }})</button>
          </template>
          确定吊销 {{ selected.length }} 个令牌？吊销后不可恢复。
        </n-popconfirm>
        <n-popconfirm v-if="selected.length" @positive-click="batchDelete">
          <template #trigger>
            <button class="btn btn-sm btn-outline" style="color:#dc2626;border-color:#dc2626">删除所选 ({{ selected.length }})</button>
          </template>
          确定永久删除 {{ selected.length }} 个令牌？此操作不可恢复！
        </n-popconfirm>
      </div>

      <!-- Key 列表表格 -->
      <div class="card" style="overflow:hidden">
        <table class="data-table" style="width:100%">
          <thead>
            <tr>
              <th style="width:40px">
                <input type="checkbox" :checked="allSelected" @change="e => selected = e.target.checked ? filteredKeysBar.map(k=>k.id) : []" />
              </th>
              <th>名称 / Key</th>
              <th style="width:90px">状态</th>
              <th style="width:180px">配额</th>
              <th style="width:130px">最后调用</th>
              <th style="width:100px">到期时间</th>
              <th style="width:150px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="k in filteredKeysBar"
              :key="k.id"
              :style="k.status==='revoked' ? 'opacity:0.6' : ''"
            >
              <td><input type="checkbox" :value="k.id" :checked="selected.includes(k.id)" @change="e => { if(e.target.checked) selected.push(k.id); else selected=selected.filter(x=>x!==k.id) }" /></td>
              <td>
                <div style="font-weight:600;font-size:13px">{{ k.name || '未命名' }}</div>
                <code style="font-size:11px;color:var(--text-secondary);font-family:var(--font-mono)">{{ k.key_prefix }}•••</code>
              </td>
              <td>
                <span :class="['badge', k.status==='active'?'badge-success':k.status==='expired'?'badge-warning':'badge-danger']">
                  {{ k.status==='active'?'有效':k.status==='expired'?'已过期':'已撤销' }}
                </span>
              </td>
              <td>
                <template v-if="k.quota_total">
                  <div style="display:flex;align-items:center;gap:6px">
                    <div style="flex:1;height:5px;background:var(--border-light);border-radius:3px;overflow:hidden">
                      <div :style="{ height:'100%', width:Math.min(100,Math.round((k.quota_used/k.quota_total)*100))+'%', background:(k.quota_used/k.quota_total)>=0.8?'#f59e0b':'var(--primary)', borderRadius:'3px' }"></div>
                    </div>
                    <span :style="{fontSize:'11px',color:'var(--text-secondary)',fontWeight:(k.quota_used/k.quota_total)>=0.8?'700':'400'}">{{ k.quota_used }}/{{ k.quota_total }}</span>
                  </div>
                </template>
                <span v-else style="font-size:12px;color:var(--text-muted)">不限</span>
              </td>
              <td style="font-size:12px;color:var(--text-secondary)">{{ k.last_used_at ? fmtDate(k.last_used_at) : '从未使用' }}</td>
              <td style="font-size:12px;color:var(--text-secondary)">{{ k.expires_at ? fmtDate(k.expires_at) : '永不过期' }}</td>
              <td>
                <div style="display:flex;gap:4px;flex-wrap:wrap">
                  <template v-if="k.status==='active'">
                    <button class="btn btn-xs btn-outline" @click="copyFullKey(k.id)">复制</button>
                    <button class="btn btn-xs btn-outline" @click="openApiCall(k)">调用</button>
                    <n-popconfirm @positive-click="revokeKey(k.id)">
                      <template #trigger><button class="btn btn-xs btn-outline" style="color:#dc2626;border-color:#dc2626">吊销</button></template>
                      确定吊销此令牌？吊销后不可恢复。
                    </n-popconfirm>
                  </template>
                  <template v-else-if="k.status==='expired'">
                    <button class="btn btn-xs btn-outline" @click="copyFullKey(k.id)">复制</button>
                    <n-popconfirm @positive-click="deleteKey(k.id)">
                      <template #trigger><button class="btn btn-xs btn-outline" style="color:#dc2626;border-color:#dc2626">删除</button></template>
                      确定永久删除此令牌？
                    </n-popconfirm>
                  </template>
                  <template v-else>
                    <button class="btn btn-xs btn-outline" disabled>已撤销</button>
                  </template>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredKeysBar.length">
              <td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted)">
                暂无数据
                <button v-if="!keys.length" class="btn btn-sm btn-primary" style="margin-left:12px" @click="showCreate=true">创建第一个 Key</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!--
        以下两个 Modal 完整保留原始代码：
        1. Create Token Modal（showCreate）— 保留所有表单字段、额度设置、访问限制、生成密钥提示
        2. API Call Modal（showApiModal）— 保留 cURL/Python/Node.js 代码示例、运行测试、AI 工具配置参考
        直接从原 Keys.vue 第 59–213 行复制粘贴，无需任何修改。
      -->
    </div>
  </template>
  ```

  > **提示：** 两个 Modal 的完整代码（`<n-modal v-model:show="showCreate">` 和 `<n-modal v-model:show="showApiModal">`）直接从原 `Keys.vue` 第 59–213 行复制，插入 `</div>` 闭合标签之前，无需任何修改。

- [ ] **4.3 验证**

  ```bash
  cd D:/code/llm-gateway/frontend && npm run dev
  ```

  打开 http://localhost:5173/keys，检查：
  - 顶部 3 格统计卡显示 Key 总数、有效 Key 数、本月调用数
  - 工具栏搜索框、状态下拉、分组下拉过滤正常
  - 有效 Key 显示绿色 `.badge-success`，已撤销显示红色 `.badge-danger`，已过期显示橙色 `.badge-warning`
  - 配额列进度条，使用率 ≥80% 变橙色且文字加粗；无配额显示"不限"
  - 已撤销行整行 `opacity:0.6` 置灰
  - 多选后批量吊销/删除按钮激活，确认弹窗正常
  - "+ 新建 API Key" 弹出创建 Modal，表单和校验与原版一致
  - "调用" 按钮弹出 API Call Modal 正常

- [ ] **4.4 提交**

  ```bash
  cd D:/code/llm-gateway
  git add frontend/src/pages/Keys.vue
  git commit -m "feat: redesign Keys page to TokenHub style with summary cards and inline quota bars"
  ```

---

## 实施顺序建议

按 Task 1 → 2 → 3 → 4 顺序执行，每个 Task 完成后单独验证再提交。Task 之间互相独立，如遇阻塞可并行处理。

## 已知注意事项

1. **`watch` 导入（Task 3）**：Step 3.1 要求将 vue import 改为包含 `watch`，否则 `watch(logs, buildStats)` 会报错。
2. **`api.getTrend` 返回结构**：`loadTrend()` 使用 `data.days` 和 `data.model_breakdown`。如实际接口字段名不同，需对应调整解构，其余逻辑不变。
3. **`allSelected` computed（Task 4）**：原 Keys.vue script 已有 `allSelected`，Task 4 模板中直接引用，无需重新定义。
4. **NCollapse / NCollapseItem 导入（Task 4）**：API Call Modal 用到这两个组件，若原 import 列表中缺少需补充 `NCollapse, NCollapseItem`。
5. **`var(--primary)` 用法**：所有颜色优先使用 CSS 变量，不硬编码 `#4f6ef7`，保持暗色模式兼容。
