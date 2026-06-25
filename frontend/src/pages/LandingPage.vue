<template>
  <div class="landing">
    <div class="hero">
      <h1 class="hero-title">API 聚合平台</h1>
      <p class="hero-subtitle">个人学习使用 · 请勿商用</p>
    </div>

    <div class="quick-cards">
      <router-link to="/playground" class="qc-item" style="--card-bg:var(--card-blue-bg);--card-accent:var(--card-blue-accent)">
        <div class="qc-icon" style="background:var(--card-blue-accent)">&#x25B6;</div>
        <div class="qc-label">快速开始</div>
        <div class="qc-desc">在线调试 API</div>
      </router-link>
      <router-link to="/models" class="qc-item" style="--card-bg:var(--card-purple-bg);--card-accent:var(--card-purple-accent)">
        <div class="qc-icon" style="background:var(--card-purple-accent)">&#x2601;</div>
        <div class="qc-label">模型广场</div>
        <div class="qc-desc">浏览可用模型</div>
      </router-link>
      <router-link to="/keys" class="qc-item" style="--card-bg:var(--card-green-bg);--card-accent:var(--card-green-accent)">
        <div class="qc-icon" style="background:var(--card-green-accent)">&#x1F511;</div>
        <div class="qc-label">API 密钥</div>
        <div class="qc-desc">管理访问凭证</div>
      </router-link>
      <router-link to="/usage" class="qc-item" style="--card-bg:var(--card-yellow-bg);--card-accent:var(--card-yellow-accent)">
        <div class="qc-icon" style="background:var(--card-yellow-accent)">&#x1F4CA;</div>
        <div class="qc-label">使用日志</div>
        <div class="qc-desc">查看调用记录</div>
      </router-link>
    </div>

    <div class="hero-stats" v-if="stats.balance !== null">
      <span>余额 <strong>¥{{ stats.balance }}</strong></span>
      <span class="stat-divider"></span>
      <span>今日调用 <strong>{{ stats.todayCalls }}</strong> 次</span>
      <span class="stat-divider"></span>
      <span>总消耗 <strong>{{ stats.totalTokens }}</strong> Tokens</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const stats = ref({ balance: null, todayCalls: 0, totalTokens: 0 })

onMounted(async () => {
  try {
    const d = await api.getDashboard()
    stats.value = {
      balance: d.balance_yuan || '0.00',
      todayCalls: d.today_calls || 0,
      totalTokens: d.total_tokens || 0,
    }
  } catch (e) { /* */ }
})
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--topbar-h) - 48px);
  padding: 0 24px;
}

.hero {
  text-align: center;
  margin-bottom: 48px;
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
  user-select: none;
}

.hero-subtitle {
  margin: 12px 0 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

/* ── Quick Cards ── */
.quick-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 680px;
  margin-bottom: 40px;
}

.qc-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 16px;
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
  font-size: 18px;
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

/* ── Stats ── */
.hero-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.hero-stats strong {
  color: var(--text);
  font-weight: 600;
}

.stat-divider {
  width: 1px;
  height: 14px;
  background: var(--border);
}

/* ── Mobile ── */
@media (max-width: 600px) {
  .quick-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
