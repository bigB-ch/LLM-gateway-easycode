<template>
  <div class="landing">
    <div class="hero">
      <h1 class="hero-title">API 聚合平台</h1>
      <p class="hero-subtitle">个人学习使用</p>
    </div>

    <div class="entry-cards">
      <router-link to="/playground" class="ec-item" style="--c:#4f6ef7">
        <div class="ec-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">在线调试</div>
          <div class="ec-desc">Playground</div>
        </div>
      </router-link>
      <router-link to="/models" class="ec-item" style="--c:#a855f7">
        <div class="ec-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">模型广场</div>
          <div class="ec-desc">浏览全部模型</div>
        </div>
      </router-link>
      <router-link to="/keys" class="ec-item" style="--c:#34d399">
        <div class="ec-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">API 密钥</div>
          <div class="ec-desc">管理访问凭证</div>
        </div>
      </router-link>
      <router-link to="/usage" class="ec-item" style="--c:#f59e0b">
        <div class="ec-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <div class="ec-info">
          <div class="ec-name">使用日志</div>
          <div class="ec-desc">查看调用记录</div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--topbar-h));
  padding: 0 24px;
}

.hero {
  text-align: center;
  margin-bottom: 56px;
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

/* ── Entry Cards ── */
.entry-cards {
  display: flex;
  gap: 16px;
  width: 100%;
  max-width: 600px;
}

.ec-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 16px 24px;
  border-radius: 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
  transition: all 0.25s ease;
  cursor: pointer;
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
  width: 48px;
  height: 48px;
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
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 2px;
}

.ec-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ── Mobile ── */
@media (max-width: 500px) {
  .entry-cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>
