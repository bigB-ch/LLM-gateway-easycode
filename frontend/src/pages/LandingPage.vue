<template>
  <div class="landing">
    <!-- Decorative background -->
    <div class="landing-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="landing-body">
      <!-- Hero -->
      <section class="hero">
        <div class="hero-bg">
          <div class="hero-shape hero-shape-1"></div>
          <div class="hero-shape hero-shape-2"></div>
          <div class="hero-shape hero-shape-3"></div>
        </div>
        <div class="hero-inner">
          <div class="hero-content">
            <div class="hero-badge">&#x2728; EasyCode 一站式 AI 平台</div>
            <h1 class="hero-title">
              <span class="ht-line">让 AI 能力</span>
              <span class="ht-line ht-accent">触手可及</span>
            </h1>
            <p class="hero-subtitle">
              提供 API Token、部署工具包、模型广场等全方位 AI 服务
              <br>从开发到部署，加速您的 AI 应用落地
            </p>
            <div class="hero-actions">
              <router-link to="/models" class="btn-primary hero-btn">
                快速开始
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
              </router-link>
              <router-link to="/custom" class="btn-outline hero-btn-outline">
                定制需求
              </router-link>
            </div>
            <div class="hero-models">
              <span class="hm-label">已接入</span>
              <span class="hm-chip">OpenAI</span>
              <span class="hm-chip">DeepSeek</span>
              <span class="hm-chip">Claude</span>
              <span class="hm-chip">Gemini</span>
              <span class="hm-sep">·</span>
              <span class="hm-more">持续接入更多模型</span>
            </div>
          </div>
          <div class="hero-visual">
            <div class="term-window">
              <div class="term-bar">
                <span class="term-dot term-dot-r"></span>
                <span class="term-dot term-dot-y"></span>
                <span class="term-dot term-dot-g"></span>
                <span class="term-title">API Demo</span>
              </div>
              <div class="term-body">
                <div class="term-line"><span class="term-prompt">$</span> curl https://api.easycode.uno/v1/chat/completions \</div>
                <div class="term-line term-indent">-H <span class="term-str">"Authorization: Bearer sk-xxxx"</span> \</div>
                <div class="term-line term-indent">-H <span class="term-str">"Content-Type: application/json"</span> \</div>
                <div class="term-line term-indent">-d <span class="term-str">'{"model":"gpt-4o","messages":[{"role":"user","content":"你好"}]}'</span></div>
                <div class="term-line term-out term-out-top">{</div>
                <div class="term-line term-out term-indent"><span class="term-key">"choices"</span>: [{</div>
                <div class="term-line term-out term-indent2"><span class="term-key">"message"</span>: {</div>
                <div class="term-line term-out term-indent3"><span class="term-key">"content"</span>: <span class="term-str">"你好！有什么可以帮助你的吗？"</span></div>
                <div class="term-line term-out term-indent2">}</div>
                <div class="term-line term-out term-indent">}]</div>
                <div class="term-line term-out">}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick stats -->
      <section class="stats-bar" v-if="tokenStats">
        <div class="stat-item">
          <span class="stat-num" v-text="tokenStats.todayCalls"></span>
          <span class="stat-lbl">今日调用</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num">&yen;{{ tokenStats.balance }}</span>
          <span class="stat-lbl">账户余额</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num" v-text="storeStats?.productCount || 0"></span>
          <span class="stat-lbl">可用工具</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num">99.9%</span>
          <span class="stat-lbl">服务可用率</span>
        </div>
      </section>

      <!-- Entry cards -->
      <section class="cards-section">
        <router-link to="/models" class="entry-card" style="--c:#4f6ef7;--c-bg:rgba(79,110,247,0.08)">
          <div class="ec-glow" style="background: radial-gradient(ellipse at center, rgba(79,110,247,0.15) 0%, transparent 70%)"></div>
          <div class="ec-icon" style="background: rgba(79,110,247,0.12);color:#4f6ef7">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          <h3 class="ec-name">API Token 业务</h3>
          <p class="ec-desc">模型广场直连，标准 OpenAI API 兼容，即接即用</p>
          <div class="ec-tags">
            <span>ChatGPT</span>
            <span>DeepSeek</span>
            <span>Claude</span>
          </div>
          <div class="ec-action">
            进入 <span class="ec-arrow">&rarr;</span>
          </div>
        </router-link>

        <router-link to="/store" class="entry-card" style="--c:#a855f7;--c-bg:rgba(168,85,247,0.08)">
          <div class="ec-glow" style="background: radial-gradient(ellipse at center, rgba(168,85,247,0.15) 0%, transparent 70%)"></div>
          <div class="ec-icon" style="background: rgba(168,85,247,0.12);color:#a855f7">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/></svg>
          </div>
          <h3 class="ec-name">Agent 安装包</h3>
          <p class="ec-desc">一键下载部署，开箱即用的 AI 工具与环境包</p>
          <div class="ec-tags">
            <span>Stable Diffusion</span>
            <span>ChatGPT-Next</span>
          </div>
          <div class="ec-action">
            浏览 <span class="ec-arrow">&rarr;</span>
          </div>
        </router-link>

        <router-link to="/custom" class="entry-card" style="--c:#f59e0b;--c-bg:rgba(245,158,11,0.08)">
          <div class="ec-glow" style="background: radial-gradient(ellipse at center, rgba(245,158,11,0.15) 0%, transparent 70%)"></div>
          <div class="ec-icon" style="background: rgba(245,158,11,0.12);color:#f59e0b">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          </div>
          <h3 class="ec-name">AI 定制</h3>
          <p class="ec-desc">从需求沟通到方案交付，端到端 AI 系统定制开发</p>
          <div class="ec-tags">
            <span>智能客服</span>
            <span>AI 动漫</span>
          </div>
          <div class="ec-action">
            了解 <span class="ec-arrow">&rarr;</span>
          </div>
        </router-link>
      </section>

      <!-- Features -->
      <section class="features-section">
        <h2 class="section-label">为什么选择 EasyCode</h2>
        <div class="features-grid">
          <div class="feat-card" style="--c:#4f6ef7;--c-bg:rgba(79,110,247,0.06)">
            <div class="feat-icon" style="background:rgba(79,110,247,0.1);color:#4f6ef7">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <h4>多模型支持</h4>
            <p>聚合主流大模型 API，统一接入标准，灵活切换</p>
          </div>
          <div class="feat-card" style="--c:#34d399;--c-bg:rgba(52,211,153,0.06)">
            <div class="feat-icon" style="background:rgba(52,211,153,0.1);color:#34d399">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            </div>
            <h4>极速响应</h4>
            <p>智能路由 + 动态负载均衡，保障低延迟高并发</p>
          </div>
          <div class="feat-card" style="--c:#f59e0b;--c-bg:rgba(245,158,11,0.06)">
            <div class="feat-icon" style="background:rgba(245,158,11,0.1);color:#f59e0b">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <h4>安全可靠</h4>
            <p>Token 鉴权 + 用量监控，数据安全有保障</p>
          </div>
          <div class="feat-card" style="--c:#a855f7;--c-bg:rgba(168,85,247,0.06)">
            <div class="feat-icon" style="background:rgba(168,85,247,0.1);color:#a855f7">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
            </div>
            <h4>开箱即用</h4>
            <p>完善的控制台 + Playground，快速测试与集成</p>
          </div>
        </div>
      </section>

      <!-- Announcements -->
      <section class="notice-section" v-if="announcements.length">
        <h2 class="section-label">平台公告</h2>
        <div class="notice-list">
          <div v-for="a in announcements" :key="a.id" class="notice-item">
            <span class="notice-dot"></span>
            <span class="notice-text">{{ a.content }}</span>
            <span class="notice-date">{{ formatDate(a.created_at) }}</span>
          </div>
        </div>
      </section>
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
/* ═══ Layout ═══ */
.landing {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 0 0 64px;
  overflow: hidden;
  min-height: calc(100vh - var(--topbar-h));
}

.landing-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  width: 100%;
  gap: 48px;
}

/* ═══ Background ═══ */
.landing-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: clip;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.bg-orb-1 {
  width: 600px; height: 600px;
  top: -200px; left: -100px;
  background: radial-gradient(circle, rgba(79,110,247,0.3) 0%, transparent 70%);
  animation: orbFloat 12s ease-in-out infinite alternate;
}

.bg-orb-2 {
  width: 400px; height: 400px;
  top: 100px; right: -80px;
  background: radial-gradient(circle, rgba(168,85,247,0.2) 0%, transparent 70%);
  animation: orbFloat 15s ease-in-out infinite alternate-reverse;
}

.bg-orb-3 {
  width: 500px; height: 500px;
  bottom: -100px; left: 20%;
  background: radial-gradient(circle, rgba(52,211,153,0.12) 0%, transparent 70%);
  animation: orbFloat 18s ease-in-out infinite alternate;
}

@keyframes orbFloat {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(60px, -40px) scale(1.15); }
}

.bg-grid {
  position: absolute;
  inset: 0;
  mask-image: radial-gradient(ellipse 90% 50% at 50% 0%, black, transparent);
  -webkit-mask-image: radial-gradient(ellipse 90% 50% at 50% 0%, black, transparent);
}

.bg-grid::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(79,110,247,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(79,110,247,0.02) 1px, transparent 1px);
  background-size: 48px 48px;
}

html.dark .bg-orb-1 {
  opacity: 0.25;
  background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%);
}
html.dark .bg-orb-2 {
  opacity: 0.2;
  background: radial-gradient(circle, rgba(168,85,247,0.2) 0%, transparent 70%);
}
html.dark .bg-orb-3 {
  opacity: 0.15;
  background: radial-gradient(circle, rgba(52,211,153,0.15) 0%, transparent 70%);
}

/* ═══ Hero ═══ */
.hero {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  width: 100%;
  background: linear-gradient(180deg, rgba(79,110,247,0.03) 0%, transparent 100%);
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(79,110,247,0.08) 0%,
    transparent 20%,
    rgba(168,85,247,0.06) 40%,
    transparent 60%,
    rgba(52,211,153,0.05) 80%,
    transparent 100%
  );
  background-size: 300% 300%;
  animation: heroGradient 8s ease-in-out infinite alternate;
  pointer-events: none;
}

@keyframes heroGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 0%; }
  100% { background-position: 50% 100%; }
}

.hero-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
}

.hero-shape-1 {
  width: 500px; height: 500px;
  top: -100px; left: -100px;
  background: radial-gradient(circle, #4f6ef7 0%, transparent 70%);
  animation: shapeFloat1 18s ease-in-out infinite alternate;
}

.hero-shape-2 {
  width: 400px; height: 400px;
  bottom: -80px; right: -60px;
  background: radial-gradient(circle, #a855f7 0%, transparent 70%);
  animation: shapeFloat2 15s ease-in-out infinite alternate;
}

.hero-shape-3 {
  width: 300px; height: 300px;
  top: 15%; left: 55%;
  background: radial-gradient(circle, #34d399 0%, transparent 70%);
  animation: shapeFloat3 20s ease-in-out infinite alternate;
}

@keyframes shapeFloat1 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(100px, 80px) scale(1.15); }
  100% { transform: translate(-40px, 40px) scale(0.95); }
}
@keyframes shapeFloat2 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-80px, -60px) scale(1.2); }
  100% { transform: translate(40px, -20px) scale(1); }
}
@keyframes shapeFloat3 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-60px, 50px) scale(1.1); }
  100% { transform: translate(30px, -30px) scale(0.9); }
}

.hero-inner {
  display: flex;
  align-items: center;
  gap: clamp(24px, 4vw, 64px);
  padding: 48px clamp(16px, 4vw, 80px);
  width: 100%;
  position: relative;
  z-index: 1;
}

.hero-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  min-width: 0;
}

.hero-visual {
  flex: 0 0 clamp(380px, 34vw, 600px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 999px;
  font-size: 0.82rem;
  color: var(--primary);
  background: rgba(79,110,247,0.08);
  border: 1px solid rgba(79,110,247,0.15);
  margin-bottom: 24px;
  letter-spacing: 0.02em;
}

.hero-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
  line-height: 1.1;
}

.ht-line {
  font-size: clamp(2.4rem, 5.5vw, 4.5rem);
  font-weight: 900;
  letter-spacing: -0.03em;
  color: var(--text);
  line-height: 1.05;
}

.ht-accent {
  background: linear-gradient(135deg, #4f6ef7 0%, #8b5cf6 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  margin: 20px 0 0;
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-secondary);
  max-width: 460px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
}

.hero-models {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 32px;
  padding: 8px 16px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  flex-wrap: wrap;
  justify-content: flex-start;
}

.hm-label {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.hm-chip {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 500;
  background: var(--primary-light);
  color: var(--primary);
}

.hm-sep {
  color: var(--border);
}

.hm-more {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  background: var(--primary);
  color: #fff;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.hero-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(79,110,247,0.3);
}

.hero-btn-outline {
  display: inline-flex;
  align-items: center;
  padding: 12px 28px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  background: transparent;
  color: var(--text);
  border: 1.5px solid var(--border);
  text-decoration: none;
  transition: all 0.2s;
}

.hero-btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-2px);
}

/* ═══ Terminal Window ═══ */
.term-window {
  width: 100%;
  border-radius: 14px;
  overflow: hidden;
  background: #1a1b2e;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow:
    0 4px 24px rgba(0,0,0,0.2),
    0 0 80px rgba(79,110,247,0.06);
  font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 0.7rem;
  line-height: 1.6;
}

.term-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.04);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.term-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.term-dot-r { background: #ff5f56; }
.term-dot-y { background: #ffbd2e; }
.term-dot-g { background: #27c93f; }

.term-title {
  margin-left: auto;
  font-size: 0.65rem;
  color: rgba(255,255,255,0.35);
  font-family: inherit;
}

.term-body {
  padding: 14px 16px;
}

.term-line {
  white-space: nowrap;
  color: #e1e1e6;
}

.term-prompt {
  color: #27c93f;
  margin-right: 8px;
  user-select: none;
}

.term-indent { padding-left: 18px; }
.term-indent2 { padding-left: 36px; }
.term-indent3 { padding-left: 54px; }

.term-str {
  color: #a78bfa;
}

.term-key {
  color: #60a5fa;
}

.term-out {
  color: rgba(225,225,230,0.5);
}

.term-out-top {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.06);
}

/* ═══ Stats bar ═══ */
.stats-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 20px 48px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 0 36px;
}

.stat-num {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.02em;
}

.stat-lbl {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: var(--border);
  flex-shrink: 0;
}

/* ═══ Entry cards ═══ */
.cards-section {
  display: flex;
  gap: 16px;
  width: 100%;
  padding: 0 clamp(16px, 4vw, 80px);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.entry-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 24px 32px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
  overflow: clip;
  cursor: pointer;
}

.ec-glow {
  position: absolute;
  top: -30%;
  left: -20%;
  width: 140%;
  height: 140%;
  opacity: 0;
  transition: opacity 0.5s;
  pointer-events: none;
}

.entry-card:hover .ec-glow {
  opacity: 1;
}

.entry-card:hover {
  transform: translateY(-8px);
  border-color: var(--c);
  box-shadow: 0 20px 48px -12px rgba(0,0,0,0.1);
}

.ec-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.25s;
}

.entry-card:hover .ec-icon {
  transform: scale(1.1);
}

.ec-name {
  font-size: 1.1rem;
  font-weight: 700;
  text-align: center;
}

.ec-desc {
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--text-secondary);
  text-align: center;
}

.ec-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  margin-top: 4px;
}

.ec-tags span {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--c-bg);
  color: var(--c);
}

.ec-action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--c);
  margin-top: 4px;
  transition: gap 0.2s;
}

.entry-card:hover .ec-action {
  gap: 8px;
}

.ec-arrow {
  transition: transform 0.2s;
}

.entry-card:hover .ec-arrow {
  transform: translateX(3px);
}

/* ═══ Features ═══ */
.features-section {
  width: 100%;
  padding: 0 clamp(16px, 4vw, 80px);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.section-label {
  text-align: center;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 28px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.feat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
  padding: 28px 16px 24px;
  border-radius: 14px;
  background:
    radial-gradient(ellipse 80% 40% at 50% 0%, color-mix(in srgb, var(--c) 12%, transparent) 0%, transparent 70%),
    var(--surface);
  border-top: 3px solid color-mix(in srgb, var(--c) 30%, transparent);
}

.feat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 24px color-mix(in srgb, var(--c) 15%, transparent);
}

.feat-card h4 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text);
}

.feat-card p {
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--text-muted);
  max-width: 240px;
}

/* ═══ Notices ═══ */
.notice-section {
  width: 100%;
  max-width: 680px;
  padding: 0 clamp(16px, 4vw, 80px);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
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
  padding: 12px 16px;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
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

/* ═══ Responsive ═══ */

@media (max-width: 960px) {
  .hero-inner {
    flex-direction: column;
    gap: 36px;
    padding: 40px 16px;
  }
  .hero-content {
    align-items: center;
    text-align: center;
  }
  .hero-subtitle {
    max-width: 85%;
  }
  .hero-models {
    justify-content: center;
  }
  .hero-visual {
    flex: 0 0 auto;
    width: 100%;
    max-width: 520px;
    min-height: auto;
  }
}

@media (max-width: 860px) {
  .stats-bar { flex-wrap: wrap; justify-content: center; gap: 8px 0; padding: 16px 24px; }
  .stat-item { padding: 4px 20px; }
  .stat-divider:nth-child(6) { display: none; }
  .cards-section { flex-direction: column; align-items: center; max-width: 420px; }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .hero-actions { flex-direction: column; }
  .features-grid { grid-template-columns: 1fr; }
  .stats-bar { gap: 0; }
  .stat-item { padding: 4px 12px; }
  .stat-num { font-size: 1.2rem; }
}
</style>
