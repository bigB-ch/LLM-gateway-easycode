<template>
  <div>
    <!-- Greeting -->
    <h1 class="page-title mb-8">欢迎回来，{{ userName }}</h1>

    <!-- 4 Stat Cards -->
    <div class="stat-grid">
      <!-- 账户数据 — blue -->
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F4B3;</div>
        <div class="stat-body">
          <div class="stat-label">当前余额</div>
          <div class="stat-value">${{ dash.balance_usd || '0.00' }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">历史消耗 ${{ dash.total_cost_usd || '0.00' }}</div>
        </div>
        <button class="btn btn-primary btn-xs" style="align-self:flex-start" @click="$router.push('/plans')">充值</button>
      </div>

      <!-- 使用统计 — green -->
      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x1F4CA;</div>
        <div class="stat-body">
          <div class="stat-label">请求次数</div>
          <div class="stat-value">{{ dash.today_calls || 0 }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">统计次数 {{ dash.total_calls || 0 }}</div>
        </div>
      </div>

      <!-- 资源消耗 — yellow -->
      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x26A1;</div>
        <div class="stat-body">
          <div class="stat-label">统计 Tokens</div>
          <div class="stat-value">{{ (dash.total_tokens || 0).toLocaleString() }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">统计额度 {{ dash.quota_used || 0 }}</div>
        </div>
      </div>

      <!-- 性能指标 — purple -->
      <div class="stat-card mc-purple">
        <div class="stat-icon">&#x23F1;</div>
        <div class="stat-body">
          <div class="stat-label">平均 RPM</div>
          <div class="stat-value">{{ dash.avg_rpm || '-' }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">平均 TPM {{ dash.avg_tpm || '-' }}</div>
        </div>
      </div>
    </div>

    <!-- Middle: Chart + Right Panels -->
    <div style="display:flex;gap:16px;margin-bottom:16px">
      <!-- Chart (75%) -->
      <div class="card card-padded" style="flex:1;min-width:0">
        <h3 class="section-title mb-12">模型数据分析</h3>
        <div class="tabs">
          <button :class="'tab ' + (chartTab === 'cost' ? 'active' : '')" @click="chartTab = 'cost'">消耗分布</button>
          <button :class="'tab ' + (chartTab === 'calls' ? 'active' : '')" @click="chartTab = 'calls'">调用趋势</button>
          <button :class="'tab ' + (chartTab === 'count' ? 'active' : '')" @click="chartTab = 'count'">调用次数分布</button>
          <button :class="'tab ' + (chartTab === 'rank' ? 'active' : '')" @click="chartTab = 'rank'">调用次数排行</button>
        </div>
        <div v-if="chartData.length" class="chart-wrap">
          <svg viewBox="0 0 600 200">
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.15"/>
                <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <polyline :points="chartPoints" fill="none" stroke="#4f6ef7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polygon :points="chartArea" fill="url(#grad)"/>
            <g v-for="(p, i) in chartData" :key="i">
              <circle :cx="x(i)" :cy="y(p.v)" r="3" fill="#4f6ef7"/>
            </g>
            <!-- X axis labels -->
            <g v-for="(p, i) in chartData" :key="'l'+i">
              <text :x="x(i)" y="198" text-anchor="middle" fill="#aaa" font-size="10">{{ p.label }}</text>
            </g>
          </svg>
        </div>
        <div v-else class="empty-state" style="padding:32px">
          <div class="empty-state-icon">&#x1F4C8;</div>
          <div class="empty-state-text">无数据</div>
          <div class="empty-state-sub">暂无调用记录，开始使用 API 后将在此显示趋势</div>
        </div>
      </div>

      <!-- Right panels (25%) -->
      <div style="width:260px;display:flex;flex-direction:column;gap:16px;flex-shrink:0">
        <!-- API 信息 -->
        <div class="card card-padded">
          <h3 class="section-title mb-12">API 信息</h3>
          <div class="empty-state" style="padding:20px 0">
            <div class="empty-state-icon" style="font-size:32px">&#x1F517;</div>
            <div class="empty-state-text" style="font-size:13px">暂无 API 信息</div>
            <div class="empty-state-sub" style="font-size:11px">请联系管理员配置上游接口密钥</div>
          </div>
        </div>

        <!-- 服务可用性 -->
        <div class="card card-padded">
          <h3 class="section-title mb-12">服务可用性</h3>
          <div class="empty-state" style="padding:20px 0">
            <div class="empty-state-icon" style="font-size:32px">&#x1F6E0;</div>
            <div class="empty-state-text" style="font-size:13px">暂无数据</div>
            <div class="empty-state-sub" style="font-size:11px">服务状态监控开发中</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: Announcements + FAQ -->
    <div style="display:flex;gap:16px">
      <!-- 系统公告 -->
      <div class="card card-padded" style="flex:1">
        <div class="flex-between mb-12">
          <h3 class="section-title">系统公告</h3>
          <span class="text-muted" style="cursor:pointer">更多 &#x203A;</span>
        </div>
        <div v-if="announcements.length">
          <div v-for="a in announcements" :key="a.id" style="padding:8px 0;border-bottom:1px solid var(--border-light)">
            <div style="font-size:13px;color:var(--text);line-height:1.5">{{ a.content }}</div>
            <div class="text-muted mt-8">{{ a.date }}</div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding:20px 0">
          <div class="empty-state-icon" style="font-size:28px">&#x1F4E3;</div>
          <div class="empty-state-text" style="font-size:13px">暂无公告</div>
        </div>
      </div>

      <!-- 常见问答 -->
      <div class="card card-padded" style="flex:1">
        <div class="flex-between mb-12">
          <h3 class="section-title">常见问答</h3>
          <span class="text-muted" style="cursor:pointer">更多 &#x203A;</span>
        </div>
        <div v-if="faqs.length">
          <div v-for="f in faqs" :key="f.id" style="padding:8px 0;border-bottom:1px solid var(--border-light);cursor:pointer" @click="f.open = !f.open">
            <div style="font-size:13px;display:flex;justify-content:space-between;align-items:center">
              <span>{{ f.q }}</span>
              <span style="color:var(--text-muted);font-size:11px">{{ f.open ? '&#x25B2;' : '&#x25BC;' }}</span>
            </div>
            <div v-if="f.open" class="text-secondary mt-8" style="font-size:12px;line-height:1.6">{{ f.a }}</div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding:20px 0">
          <div class="empty-state-icon" style="font-size:28px">&#x2753;</div>
          <div class="empty-state-text" style="font-size:13px">暂无问答</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const userName = ref('')
const chartTab = ref('cost')

const dash = ref({
  balance_usd: '0.00',
  total_cost_usd: '0.00',
  today_calls: 0,
  total_calls: 0,
  total_tokens: 0,
  quota_used: 0,
  avg_rpm: '-',
  avg_tpm: '-',
})

const announcements = ref([
  { id: 1, content: '已同步 deepseek-v4-flash / deepseek-v4-pro 模型，欢迎使用', date: '2026-06-03' },
  { id: 2, content: 'DeepSeek V4 系列模型性能大幅提升，建议升级至最新版本', date: '2026-06-01' },
  { id: 3, content: '系统维护通知：本周六凌晨 2:00-4:00 进行例行维护', date: '2026-05-28' },
])

const faqs = ref([
  { id: 1, q: '如何创建 API 令牌？', a: '进入「令牌管理」页面，点击「添加令牌」按钮即可创建。令牌仅在创建时完整显示一次，请立即保存。', open: false },
  { id: 2, q: '如何充值？', a: '前往「钱包管理」页面选择套餐购买。当前支持多种面额，支付完成后余额即时到账。', open: false },
  { id: 3, q: '支持哪些模型？', a: '支持 DeepSeek V4（flash/pro）、OpenAI GPT-4o、Claude 等主流模型，可在 Playground 中测试。', open: false },
])

// Chart mock data
const chartData = computed(() => {
  if (chartTab.value === 'cost') {
    return [
      { label: '00:00', v: 0.12 }, { label: '04:00', v: 0.05 }, { label: '08:00', v: 0.32 },
      { label: '12:00', v: 0.58 }, { label: '16:00', v: 0.41 }, { label: '20:00', v: 0.23 }, { label: '24:00', v: 0.08 },
    ]
  }
  if (chartTab.value === 'calls') {
    return [
      { label: '00:00', v: 25 }, { label: '04:00', v: 10 }, { label: '08:00', v: 65 },
      { label: '12:00', v: 120 }, { label: '16:00', v: 85 }, { label: '20:00', v: 45 }, { label: '24:00', v: 15 },
    ]
  }
  if (chartTab.value === 'count') {
    return [
      { label: '00:00', v: 12 }, { label: '04:00', v: 5 }, { label: '08:00', v: 38 },
      { label: '12:00', v: 55 }, { label: '16:00', v: 42 }, { label: '20:00', v: 28 }, { label: '24:00', v: 8 },
    ]
  }
  return [
    { label: 'GPT-4o', v: 350 }, { label: 'DS-flash', v: 280 }, { label: 'DS-pro', v: 180 },
    { label: 'Claude', v: 120 }, { label: 'Gemini', v: 80 }, { label: 'GPT-4', v: 60 }, { label: 'Other', v: 30 },
  ]
})

const maxVal = computed(() => Math.max(...chartData.value.map(d => d.v), 1))

function x(i) { return 55 + (i / (chartData.value.length - 1)) * 490 }
function y(v) { return 170 - (v / maxVal.value) * 140 }

const chartPoints = computed(() =>
  chartData.value.map((d, i) => `${x(i)},${y(d.v)}`).join(' ')
)
const chartArea = computed(() =>
  `${x(0)},170 ` + chartData.value.map((d, i) => `${x(i)},${y(d.v)}`).join(' ') + ` ${x(chartData.value.length - 1)},170`
)

onMounted(async () => {
  try {
    const user = await api.getMe()
    userName.value = user.username || user.email || ''
    const d = await api.getDashboard()
    dash.value = { ...dash.value, ...d }
  } catch (e) { /* */ }
})
</script>
