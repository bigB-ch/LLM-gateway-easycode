<template>
  <div>
    <h1 class="page-title mb-8">{{ t('welcomeBack') }}，{{ userName }}</h1>
    <div class="stat-grid">
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F4B3;</div>
        <div class="stat-body">
          <div class="stat-label">{{ t('balance') }}</div>
          <div class="stat-value">&yen;{{ dash.balance_yuan || '0.00' }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">{{ t('totalSpent') }} &yen;{{ dash.total_cost_yuan || '0.00' }}</div>
        </div>
        <button class="btn btn-primary btn-xs" style="align-self:flex-start" @click="$router.push('/plans')">{{ t('topUp') }}</button>
      </div>
      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x1F4CA;</div>
        <div class="stat-body">
          <div class="stat-label">{{ t('requests') }}</div>
          <div class="stat-value">{{ dash.today_calls || 0 }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">{{ t('totalCalls') }} {{ dash.total_calls || 0 }}</div>
        </div>
      </div>
      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x26A1;</div>
        <div class="stat-body">
          <div class="stat-label">{{ t('totalTokens') }}</div>
          <div class="stat-value">{{ (dash.total_tokens || 0).toLocaleString() }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">{{ t('allTime') }}</div>
        </div>
      </div>
      <div class="stat-card mc-purple">
        <div class="stat-icon">&#x23F1;</div>
        <div class="stat-body">
          <div class="stat-label">{{ t('activeKeys') }}</div>
          <div class="stat-value">{{ dash.key_count || '-' }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:2px">API Keys</div>
        </div>
      </div>
    </div>
    <div style="display:flex;gap:16px;margin-bottom:16px">
      <div class="card card-padded" style="flex:1;min-width:0">
        <h3 class="section-title mb-12">{{ t('spendingTrend') }}</h3>
        <div v-if="trendData.length" class="chart-wrap">
          <svg viewBox="0 0 600 200"><defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--primary)" stop-opacity="0.15"/><stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/></linearGradient></defs><polyline :points="chartPoints" fill="none" stroke="#4f6ef7" stroke-width="2"/><polygon :points="chartArea" fill="url(#grad)"/><g v-for="(p,i) in trendData" :key="i"><circle :cx="x(i)" :cy="y(p.cost_yuan)" r="3" fill="#4f6ef7"/></g><g v-for="(p,i) in trendData" :key="'l'+i"><text :x="x(i)" y="195" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text></g></svg>
        </div>
        <div v-else class="empty-state" style="padding:32px"><div class="empty-state-icon">&#x1F4C8;</div><div class="empty-state-text">{{ t('noData') }}</div><div class="empty-state-sub">{{ t('trendHint') }}</div></div>
      </div>
      <div style="width:260px;display:flex;flex-direction:column;gap:16px;flex-shrink:0">
        <div class="card card-padded"><h3 class="section-title mb-12">{{ t('apiInfo') }}</h3><div style="font-size:12px;line-height:1.8;color:var(--text-secondary)"><div>{{ t('apiBaseUrl') }}: <code style="font-size:11px">/v1</code></div><div>{{ t('apiAuth') }}: <code style="font-size:11px">Bearer sk-...</code></div><div>{{ t('apiFormat') }}: {{ t('apiFormatVal') }}</div></div></div>
        <div class="card card-padded"><h3 class="section-title mb-12">{{ t('quickLinks') }}</h3><div style="display:flex;flex-direction:column;gap:6px"><a href="/keys" style="font-size:12px;color:var(--primary)">{{ t('createKey') }}</a><a href="/playground" style="font-size:12px;color:var(--primary)">{{ t('testPlayground') }}</a><a href="/models" style="font-size:12px;color:var(--primary)">{{ t('browseModels') }}</a></div></div>
      </div>
    </div>
    <div style="display:flex;gap:16px">
      <div class="card card-padded" style="flex:1"><h3 class="section-title mb-12">{{ t('announcements') }}</h3><div v-if="announcements.length"><div v-for="a in announcements" :key="a.id" style="padding:8px 0;border-bottom:1px solid var(--border-light)"><div style="font-size:13px;line-height:1.5">{{ a.content }}</div><div class="text-muted mt-8" style="font-size:11px">{{ a.date }}</div></div></div><div v-else class="empty-state" style="padding:20px 0"><div class="empty-state-icon" style="font-size:28px">&#x1F4E3;</div><div class="empty-state-text" style="font-size:13px">{{ t('noAnnouncements') }}</div></div></div>
      <div class="card card-padded" style="flex:1"><h3 class="section-title mb-12">{{ t('faq') }}</h3><div v-if="faqs.length"><div v-for="f in faqs" :key="f.id" style="padding:8px 0;border-bottom:1px solid var(--border-light);cursor:pointer" @click="f.open=!f.open"><div style="font-size:13px;display:flex;justify-content:space-between;align-items:center"><span>{{ f.q }}</span><span style="color:var(--text-muted);font-size:11px">{{ f.open?'&#x25B2;':'&#x25BC;' }}</span></div><div v-if="f.open" class="text-secondary mt-8" style="font-size:12px;line-height:1.6">{{ f.a }}</div></div></div><div v-else class="empty-state" style="padding:20px 0"><div class="empty-state-icon" style="font-size:28px">&#x2753;</div><div class="empty-state-text" style="font-size:13px">{{ t('noFaq') }}</div></div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()
const userName = ref(''); const dash = ref({}); const trendData = ref([])
const announcements = ref([]); const faqs = ref([])
const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))
function x(i) { return 40 + (i / Math.max(trendData.value.length - 1, 1)) * 520 }
function y(v) { return 170 - ((v || 0) / maxCost.value) * 140 }
const chartPoints = computed(() => trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' '))
const chartArea = computed(() => `${x(0)},170 ` + trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' ') + ` ${x(Math.max(trendData.value.length - 1, 0))},170`)
onMounted(async () => {
  try { const u = await api.getMe(); userName.value = u.username || u.email || '' } catch(e){}
  try { const d = await api.getDashboard(); dash.value = { ...dash.value, ...d } } catch(e){}
  try { const tr = await api.getTrend(7); trendData.value = tr.trend || [] } catch(e){}
  try { const a = await api.getAnnouncements(); announcements.value = (a.items||[]).map(x=>({...x,open:false})) } catch(e){}
  try { const f = await api.getFAQ(); faqs.value = (f.items||[]).map(x=>({...x,open:false})) } catch(e){}
})
</script>
