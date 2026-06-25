<template>
  <div class="landing">
    <!-- Hero -->
    <div class="hero">
      <h1 class="hero-title">API 聚合平台</h1>
      <p class="hero-subtitle">个人学习使用</p>
      <div class="hero-metrics" v-if="metrics">
        <div class="hm-item">
          <span class="hm-num">{{ metrics.modelCount }}+</span>
          <span class="hm-label">可用模型</span>
        </div>
        <div class="hm-dot"></div>
        <div class="hm-item">
          <span class="hm-num">{{ metrics.lowestPrice }}</span>
          <span class="hm-label">每百万 Token 起</span>
        </div>
        <div class="hm-dot"></div>
        <div class="hm-item">
          <span class="hm-num">{{ metrics.providerCount }}</span>
          <span class="hm-label">供应商</span>
        </div>
      </div>
    </div>

    <!-- User Stats -->
    <div class="user-stats" v-if="stats.balance !== null">
      <div class="us-item" style="background:var(--card-blue-bg);border-left-color:var(--card-blue-accent)">
        <span class="us-label">账户余额</span>
        <span class="us-value" style="color:var(--card-blue-accent)">¥{{ stats.balance }}</span>
      </div>
      <div class="us-item" style="background:var(--card-green-bg);border-left-color:var(--card-green-accent)">
        <span class="us-label">今日调用</span>
        <span class="us-value" style="color:var(--card-green-accent)">{{ stats.todayCalls }}</span>
      </div>
      <div class="us-item" style="background:var(--card-purple-bg);border-left-color:var(--card-purple-accent)">
        <span class="us-label">消耗 Tokens</span>
        <span class="us-value" style="color:var(--card-purple-accent)">{{ fmtTokens(stats.totalTokens) }}</span>
      </div>
      <div class="us-item" style="background:var(--card-yellow-bg);border-left-color:var(--card-yellow-accent)">
        <span class="us-label">有效密钥</span>
        <span class="us-value" style="color:var(--card-yellow-accent)">{{ stats.keyCount }}</span>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="section-label">快捷入口</div>
    <div class="quick-cards">
      <router-link to="/playground" class="qc-item" style="--card-bg:var(--card-blue-bg);--card-accent:var(--card-blue-accent)">
        <div class="qc-icon" style="background:var(--card-blue-accent)">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        </div>
        <div class="qc-label">在线调试</div>
        <div class="qc-desc">Playground</div>
      </router-link>
      <router-link to="/models" class="qc-item" style="--card-bg:var(--card-purple-bg);--card-accent:var(--card-purple-accent)">
        <div class="qc-icon" style="background:var(--card-purple-accent)">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        </div>
        <div class="qc-label">模型广场</div>
        <div class="qc-desc">浏览全部模型</div>
      </router-link>
      <router-link to="/keys" class="qc-item" style="--card-bg:var(--card-green-bg);--card-accent:var(--card-green-accent)">
        <div class="qc-icon" style="background:var(--card-green-accent)">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
        </div>
        <div class="qc-label">API 密钥</div>
        <div class="qc-desc">管理凭证</div>
      </router-link>
      <router-link to="/usage" class="qc-item" style="--card-bg:var(--card-yellow-bg);--card-accent:var(--card-yellow-accent)">
        <div class="qc-icon" style="background:var(--card-yellow-accent)">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <div class="qc-label">使用日志</div>
        <div class="qc-desc">查看调用记录</div>
      </router-link>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const stats = ref({ balance: null, todayCalls: 0, totalTokens: 0, keyCount: 0 })
const metrics = ref(null)

function fmtTokens(n) {
  if (!n) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

onMounted(async () => {
  try {
    const d = await api.getDashboard()
    stats.value = {
      balance: d.balance_yuan || '0.00',
      todayCalls: d.today_calls || 0,
      totalTokens: d.total_tokens || 0,
      keyCount: d.key_count || 0,
    }
    metrics.value = {
      modelCount: 0,
      providerCount: 0,
      lowestPrice: '—',
    }
  } catch (e) { /* */ }
})
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 24px 64px;
  min-height: calc(100vh - var(--topbar-h) - 48px);
}

/* ── Hero ── */
.hero {
  text-align: center;
  margin-bottom: 36px;
  max-width: 700px;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 5rem);
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: 0.06em;
  margin: 0;
  background: linear-gradient(135deg, #4f6ef7 0%, #8b5cf6 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  margin: 12px 0 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.hero-metrics {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-top: 28px;
}

.hm-item {
  text-align: center;
}

.hm-num {
  display: block;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
}

.hm-label {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.hm-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--border);
  flex-shrink: 0;
}

/* ── User Stats ── */
.user-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
  max-width: 800px;
  margin-bottom: 36px;
}

.us-item {
  padding: 16px;
  border-radius: 10px;
  border-left: 3px solid;
  text-align: center;
}

.us-label {
  display: block;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.us-value {
  font-size: 1.3rem;
  font-weight: 700;
}

/* ── Section Label ── */
.section-label {
  width: 100%;
  max-width: 800px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 12px;
  padding-left: 4px;
}

/* ── Quick Cards ── */
.quick-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
  max-width: 800px;
  margin-bottom: 36px;
}

.qc-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 12px;
  border-radius: 12px;
  background: var(--card-bg);
  border-left: 3px solid var(--card-accent);
  text-decoration: none;
  color: var(--text);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.qc-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.qc-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.qc-label {
  font-size: 0.9rem;
  font-weight: 600;
}

.qc-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ── Mobile ── */
@media (max-width: 700px) {
  .user-stats { grid-template-columns: repeat(2, 1fr); }
  .quick-cards { grid-template-columns: repeat(2, 1fr); }
  .hero-metrics { gap: 16px; }
}
</style>
