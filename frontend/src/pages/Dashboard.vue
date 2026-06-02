<template>
  <div>
    <!-- 4 Macaron Stat Cards -->
    <div class="stat-grid">
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F4B3;</div>
        <div class="stat-body">
          <div class="stat-value">&yen;{{ dash.balance_yuan }}</div>
          <div class="stat-label">账户余额</div>
        </div>
        <button class="btn btn-outline btn-sm">充值</button>
      </div>

      <div class="stat-card mc-purple">
        <div class="stat-icon">&#x26A1;</div>
        <div class="stat-body">
          <div class="stat-value">{{ dash.today_calls }}</div>
          <div class="stat-label">今日调用</div>
        </div>
      </div>

      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x1F4CA;</div>
        <div class="stat-body">
          <div class="stat-value">&yen;{{ dash.today_cost_yuan }}</div>
          <div class="stat-label">今日消费</div>
        </div>
      </div>

      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x23F1;</div>
        <div class="stat-body">
          <div class="stat-value">{{ dash.avg_latency_ms || '-' }}<span style="font-size:14px;font-weight:400;color:var(--text-secondary)"> ms</span></div>
          <div class="stat-label">平均延迟</div>
        </div>
      </div>
    </div>

    <!-- Chart + API Info row -->
    <div style="display:flex;gap:16px;margin-bottom:20px">
      <!-- Chart Card -->
      <div class="card card-padded" style="flex:1">
        <div class="tabs">
          <button :class="'tab ' + (chartTab === 'cost' ? 'active' : '')" @click="chartTab = 'cost'">消耗分布</button>
          <button :class="'tab ' + (chartTab === 'calls' ? 'active' : '')" @click="chartTab = 'calls'">调用趋势</button>
        </div>
        <div v-if="chartData.length" class="chart-wrap">
          <svg viewBox="0 0 600 200">
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.12"/>
                <stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <polyline
              :points="chartPoints"
              fill="none"
              stroke="#4f6ef7"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <polygon
              :points="chartArea"
              fill="url(#grad)"
            />
            <g v-for="(p, i) in chartData" :key="i">
              <circle :cx="x(i)" :cy="y(p.v)" r="3" fill="#4f6ef7" />
            </g>
          </svg>
        </div>
        <div v-else class="empty-state" style="padding:32px">
          <div class="empty-state-icon">&#x1F4C8;</div>
          <div class="empty-state-text">暂无数据</div>
          <div class="empty-state-sub">开始使用 API 后将在此显示趋势</div>
        </div>
      </div>

      <!-- API Info Card -->
      <div class="card card-padded" style="width:280px">
        <h3 class="section-title mb-16">API 信息</h3>
        <div class="text-secondary mb-8">Base URL</div>
        <div class="inline-code" style="display:block;word-break:break-all;margin-bottom:16px">{{ apiBase }}/v1</div>
        <div class="text-secondary mb-8">认证方式</div>
        <div class="text-secondary">Bearer Token (API Key)</div>
        <div style="margin-top:16px">
          <a href="#" class="btn btn-outline btn-sm" style="width:100%">查看文档 &#x2197;</a>
        </div>
      </div>
    </div>

    <!-- Bottom row: Announcements + FAQ -->
    <div style="display:flex;gap:16px">
      <div class="card card-padded" style="flex:1">
        <div class="flex-between mb-16">
          <h3 class="section-title">系统公告</h3>
          <span class="text-muted">更多 &#x203A;</span>
        </div>
        <div v-if="announcements.length">
          <div v-for="a in announcements" :key="a.id" style="padding:10px 0;border-bottom:1px solid var(--border-light)">
            <div style="font-size:14px;color:var(--text)">{{ a.title }}</div>
            <div class="text-muted mt-8">{{ a.date }}</div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding:24px">
          <div class="empty-state-icon" style="font-size:36px">&#x1F4E3;</div>
          <div class="empty-state-text">暂无公告</div>
        </div>
      </div>

      <div class="card card-padded" style="flex:1">
        <div class="flex-between mb-16">
          <h3 class="section-title">常见问题</h3>
          <span class="text-muted">更多 &#x203A;</span>
        </div>
        <div v-if="faqs.length">
          <div v-for="f in faqs" :key="f.id" style="padding:10px 0;border-bottom:1px solid var(--border-light);cursor:pointer" @click="f.open = !f.open">
            <div style="font-size:14px;display:flex;justify-content:space-between;align-items:center">
              <span>{{ f.q }}</span>
              <span style="color:var(--text-muted)">{{ f.open ? '&#x25B2;' : '&#x25BC;' }}</span>
            </div>
            <div v-if="f.open" class="text-secondary mt-8" style="line-height:1.6">{{ f.a }}</div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding:24px">
          <div class="empty-state-icon" style="font-size:36px">&#x2753;</div>
          <div class="empty-state-text">暂无常见问题</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const dash = ref({ balance_yuan: 0, today_calls: 0, today_cost_yuan: 0, avg_latency_ms: null })
const chartTab = ref('cost')
const apiBase = window.location.origin

const announcements = ref([])
const faqs = ref([
  { id: 1, q: '如何获取 API Key？', a: '登录后在「令牌管理」页面创建新的 API Key，创建后请立即复制保存。', open: false },
  { id: 2, q: '如何充值？', a: '前往「钱包管理」页面选择套餐购买，支持多种面额。支付完成后余额即时到账。', open: false },
  { id: 3, q: '支持哪些模型？', a: '支持 OpenAI、Anthropic、Google、DeepSeek 等主流供应商的模型，可在 Playground 中测试。', open: false },
])

// Mock chart data — will be replaced with real API data
const chartData = computed(() => {
  if (chartTab.value === 'cost') {
    return [
      { label: 'Mon', v: 12 }, { label: 'Tue', v: 8 }, { label: 'Wed', v: 22 },
      { label: 'Thu', v: 15 }, { label: 'Fri', v: 30 }, { label: 'Sat', v: 5 }, { label: 'Sun', v: 18 },
    ]
  }
  return [
    { label: 'Mon', v: 80 }, { label: 'Tue', v: 55 }, { label: 'Wed', v: 140 },
    { label: 'Thu', v: 95 }, { label: 'Fri', v: 200 }, { label: 'Sat', v: 30 }, { label: 'Sun', v: 110 },
  ]
})

const maxVal = computed(() => Math.max(...chartData.value.map(d => d.v), 1))

function x(i) { return 50 + (i / (chartData.value.length - 1)) * 500 }
function y(v) { return 180 - (v / maxVal.value) * 150 }

const chartPoints = computed(() =>
  chartData.value.map((d, i) => `${x(i)},${y(d.v)}`).join(' ')
)

const chartArea = computed(() =>
  `${x(0)},180 ` + chartData.value.map((d, i) => `${x(i)},${y(d.v)}`).join(' ') + ` ${x(chartData.value.length - 1)},180`
)

onMounted(async () => {
  try {
    dash.value = await api.getDashboard()
  } catch (e) { console.error(e) }
})
</script>
