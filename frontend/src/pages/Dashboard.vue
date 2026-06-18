<template>
  <div>
    <n-h1 style="margin-bottom:8px">
      {{ t('welcomeBack') }}，{{ userName }}
    </n-h1>

    <!-- Stat cards -->
    <n-grid :x-gap="16" :y-gap="16" :cols="2" :item-responsive="true" style="margin-bottom:16px">
      <n-grid-item span="1">
        <n-card size="small" :bordered="true">
          <n-space align="center" justify="space-between">
            <div>
              <n-statistic :label="t('balance')" :value="'¥' + (dash.balance_yuan || '0.00')" />
              <n-text depth="3" style="font-size:11px">{{ t('totalSpent') }} ¥{{ dash.total_cost_yuan || '0.00' }}</n-text>
            </div>
            <n-button size="small" type="primary" @click="$router.push('/plans')">{{ t('topUp') }}</n-button>
          </n-space>
        </n-card>
      </n-grid-item>
      <n-grid-item span="1">
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('requests')" :value="(dash.today_calls || 0).toLocaleString()">
            <template #suffix>
              <n-text depth="3" style="font-size:11px;margin-left:8px">{{ t('totalCalls') }} {{ (dash.total_calls || 0).toLocaleString() }}</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item span="1">
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('totalTokens')" :value="(dash.total_tokens || 0).toLocaleString()">
            <template #suffix>
              <n-text depth="3" style="font-size:11px;margin-left:8px">{{ t('allTime') }}</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item span="1">
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('activeKeys')" :value="dash.key_count || '-'" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- Trend + Sidebar -->
    <n-space :size="16" style="margin-bottom:16px" item-style="min-width:0">
      <n-card :bordered="true" style="flex:1">
        <n-h3 style="margin:0 0 12px">{{ t('spendingTrend') }}</n-h3>
        <div v-if="trendData.length" class="chart-wrap" style="width:100%">
          <svg viewBox="0 0 600 200" style="width:100%;height:auto">
            <defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--primary)" stop-opacity="0.15"/><stop offset="100%" stop-color="var(--primary)" stop-opacity="0"/></linearGradient></defs>
            <polyline :points="chartPoints" fill="none" stroke="#4f6ef7" stroke-width="2"/>
            <polygon :points="chartArea" fill="url(#grad)"/>
            <g v-for="(p,i) in trendData" :key="i"><circle :cx="x(i)" :cy="y(p.cost_yuan)" r="3" fill="#4f6ef7"/></g>
            <g v-for="(p,i) in trendData" :key="'l'+i"><text :x="x(i)" y="195" text-anchor="middle" fill="#aaa" font-size="10">{{ p.date.slice(5) }}</text></g>
          </svg>
        </div>
        <n-empty v-else :description="t('trendHint')" style="padding:32px 0" />
      </n-card>
      <n-space vertical :size="16" style="width:260px;flex-shrink:0">
        <n-card :bordered="true" size="small">
          <n-h3 style="margin:0 0 12px">{{ t('apiInfo') }}</n-h3>
          <n-space vertical :size="4">
            <n-text depth="2" style="font-size:12px">{{ t('apiBaseUrl') }}: <n-code> /v1</n-code></n-text>
            <n-text depth="2" style="font-size:12px">{{ t('apiAuth') }}: <n-code>Bearer sk-...</n-code></n-text>
            <n-text depth="2" style="font-size:12px">{{ t('apiFormat') }}: {{ t('apiFormatVal') }}</n-text>
          </n-space>
        </n-card>
        <n-card :bordered="true" size="small">
          <n-h3 style="margin:0 0 12px">{{ t('quickLinks') }}</n-h3>
          <n-space vertical :size="6">
            <a href="/keys" style="font-size:12px;color:var(--primary)">{{ t('createKey') }}</a>
            <a href="/playground" style="font-size:12px;color:var(--primary)">{{ t('testPlayground') }}</a>
            <a href="/models" style="font-size:12px;color:var(--primary)">{{ t('browseModels') }}</a>
          </n-space>
        </n-card>
      </n-space>
    </n-space>

    <!-- Announcements + FAQ -->
    <n-space :size="16">
      <n-card :bordered="true" style="flex:1">
        <n-h3 style="margin:0 0 12px">{{ t('announcements') }}</n-h3>
        <div v-if="announcements.length">
          <div v-for="a in announcements" :key="a.id" style="padding:8px 0;border-bottom:1px solid var(--border-light)">
            <div style="font-size:13px;line-height:1.5">{{ a.content }}</div>
            <n-text depth="3" style="font-size:11px;margin-top:8px;display:block">{{ a.date }}</n-text>
          </div>
        </div>
        <n-empty v-else :description="t('noAnnouncements')" style="padding:20px 0" />
      </n-card>
      <n-card :bordered="true" style="flex:1">
        <n-h3 style="margin:0 0 12px">{{ t('faq') }}</n-h3>
        <n-collapse v-if="faqs.length" :expanded-names="expandedFaq" @update:expanded-names="expandedFaq=$event">
          <n-collapse-item v-for="f in faqs" :key="f.id" :name="f.id" :title="f.q">
            <n-text depth="2" style="font-size:12px;line-height:1.6">{{ f.a }}</n-text>
          </n-collapse-item>
        </n-collapse>
        <n-empty v-else :description="t('noFaq')" style="padding:20px 0" />
      </n-card>
    </n-space>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NCollapse, NCollapseItem, NEmpty, NGrid, NGridItem,
  NH1, NH3, NCode, NSpace, NStatistic, NText, NButton,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()
const userName = ref('')
const dash = ref({})
const trendData = ref([])
const dayDetails = ref([])
const announcements = ref([])
const faqs = ref([])
const expandedFaq = ref([])

const maxCost = computed(() => Math.max(...trendData.value.map(d => d.cost_yuan || 0), 1))
function x(i) { return 40 + (i / Math.max(trendData.value.length - 1, 1)) * 520 }
function y(v) { return 170 - ((v || 0) / maxCost.value) * 140 }
const chartPoints = computed(() => trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' '))
const chartArea = computed(() =>
  `${x(0)},170 ` + trendData.value.map((d, i) => `${x(i)},${y(d.cost_yuan)}`).join(' ') +
  ` ${x(Math.max(trendData.value.length - 1, 0))},170`
)

onMounted(async () => {
  try { const u = await api.getMe(); userName.value = u.username || u.email || '' } catch (e) { /* */ }
  try { const d = await api.getDashboard(); dash.value = { ...dash.value, ...d } } catch (e) { /* */ }
  try { const tr = await api.getTrend(7); trendData.value = tr.trend || []; dayDetails.value = tr.details || [] } catch (e) { /* */ }
  try { const a = await api.getAnnouncements(); announcements.value = (a.items || []).map(x => ({ ...x, open: false })) } catch (e) { /* */ }
  try { const f = await api.getFAQ(); faqs.value = (f.items || []).map(x => ({ ...x, open: false })) } catch (e) { /* */ }
})
</script>
