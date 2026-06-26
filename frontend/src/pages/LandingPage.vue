<template>
  <div class="landing">
    <div class="hero">
      <h1 class="hero-title">AI 工具超市</h1>
      <p class="hero-subtitle">一站式 AI 工具与服务平台</p>
    </div>

    <div class="entry-cards">
      <router-link to="/dashboard" class="ec-item" style="--c:#4f6ef7">
        <div class="ec-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">Token 买卖</div>
          <div class="ec-desc">LLM API 中转服务</div>
        </div>
        <div class="ec-stats" v-if="tokenStats">
          <span>余额 ¥{{ tokenStats.balance }}</span>
          <span>今日 {{ tokenStats.todayCalls }} 次</span>
        </div>
        <div class="ec-action">进入 &rarr;</div>
      </router-link>

      <router-link to="/store" class="ec-item" style="--c:#a855f7">
        <div class="ec-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">Agent 安装包</div>
          <div class="ec-desc">一键下载部署</div>
        </div>
        <div class="ec-stats" v-if="storeStats">
          <span>{{ storeStats.productCount }} 款可用</span>
        </div>
        <div class="ec-action">进入 &rarr;</div>
      </router-link>

      <router-link to="/custom" class="ec-item" style="--c:#f59e0b">
        <div class="ec-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">AI 定制</div>
          <div class="ec-desc">按需定制开发</div>
        </div>
        <div class="ec-action">了解 &rarr;</div>
      </router-link>
    </div>

    <div class="bottom-section" v-if="announcements.length">
      <h3 class="section-title">平台公告</h3>
      <div class="notice-list">
        <div v-for="a in announcements" :key="a.id" class="notice-item">
          <span class="notice-dot"></span>
          <span class="notice-text">{{ a.content }}</span>
          <span class="notice-date">{{ formatDate(a.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const tokenStats = ref(null)
const storeStats = ref(null)
const announcements = ref([])

function formatDate(iso) {
  if (!iso) return ''
  return iso.slice(0, 10)
}

onMounted(async () => {
  try {
    const d = await api.getDashboard()
    tokenStats.value = {
      balance: d.balance_yuan || '0.00',
      todayCalls: d.today_calls || 0,
    }
  } catch (_) {}

  try {
    const s = await api.listProducts()
    storeStats.value = {
      productCount: s.items?.length || 0,
    }
  } catch (_) {}

  try {
    const a = await api.getAnnouncements()
    announcements.value = a.items || []
  } catch (_) {}
})
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px 64px;
  min-height: calc(100vh - var(--topbar-h));
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
}

.hero-subtitle {
  margin: 12px 0 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.entry-cards {
  display: flex;
  gap: 20px;
  width: 100%;
  max-width: 800px;
}

.ec-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 36px 20px 28px;
  border-radius: 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.ec-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--c);
  opacity: 0.5;
}

.ec-item:hover {
  transform: translateY(-6px);
  border-color: var(--c);
  box-shadow: 0 12px 32px -8px rgba(0,0,0,0.12);
}

.ec-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c) 10%, transparent);
  color: var(--c);
}

.ec-info {
  text-align: center;
}

.ec-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 2px;
}

.ec-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.ec-stats {
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.ec-action {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--c);
  margin-top: 4px;
}

.bottom-section {
  width: 100%;
  max-width: 800px;
  margin-top: 48px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--text);
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notice-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--bg-secondary, #f8f9fb);
  font-size: 0.85rem;
}

.notice-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  flex-shrink: 0;
}

.notice-text { flex: 1; color: var(--text); }
.notice-date { color: var(--text-muted); font-size: 0.75rem; flex-shrink: 0; }

@media (max-width: 640px) {
  .entry-cards { flex-direction: column; max-width: 400px; }
}
</style>
