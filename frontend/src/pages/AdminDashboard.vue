<template>
  <div>
    <h1 class="page-title mb-24">{{ t('platformOverview') }}</h1>

    <div class="stat-grid">
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F465;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">{{ t('totalUsers') }}</div>
        </div>
      </div>
      <div class="stat-card mc-purple">
        <div class="stat-icon">&#x26A1;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.today_calls }}</div>
          <div class="stat-label">{{ t('todayCalls') }}</div>
        </div>
      </div>
      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x1F4B0;</div>
        <div class="stat-body">
          <div class="stat-value">&yen;{{ stats.today_revenue_yuan }}</div>
          <div class="stat-label">{{ t('todayRevenue') }}</div>
        </div>
      </div>
      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x2699;&#xFE0F;</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.active_suppliers }}</div>
          <div class="stat-label">{{ t('activeSuppliers') }}</div>
        </div>
      </div>
    </div>

    <!-- Two-column detail -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:24px">
      <!-- Top models -->
      <div class="card card-padded">
        <h3 class="section-title mb-16">{{ t('todayTopModels') }}</h3>
        <div v-if="stats.top_models && stats.top_models.length > 0">
          <div v-for="(m, i) in stats.top_models" :key="m.model" class="flex-between" style="padding:8px 0;border-bottom:1px solid var(--border-light)">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-weight:700;font-size:14px;color:var(--text-secondary)">{{ i + 1 }}</span>
              <span style="font-weight:500">{{ m.model }}</span>
            </div>
            <span style="font-weight:600;font-size:13px">{{ m.count }} 次</span>
          </div>
        </div>
        <div v-else class="text-muted text-center" style="padding:20px">{{ t('breakersNoData') }}</div>
      </div>

      <!-- Recent calls -->
      <div class="card card-padded">
        <h3 class="section-title mb-16">{{ t('recentCalls') }}</h3>
        <div v-if="stats.recent_calls && stats.recent_calls.length > 0">
          <div v-for="log in stats.recent_calls.slice(0, 8)" :key="log.id" class="flex-between" style="padding:6px 0;border-bottom:1px solid var(--border-light);font-size:12px">
            <div style="flex:1;min-width:0">
              <span style="font-weight:500">{{ log.model }}</span>
              <span class="text-muted" style="margin-left:4px">{{ log.provider }}</span>
            </div>
            <div style="display:flex;gap:12px;align-items:center;flex-shrink:0">
              <span :class="'badge ' + (log.status === 'success' ? 'badge-success' : 'badge-danger')" style="font-size:9px">{{ log.status === 'success' ? '成功' : '失败' }}</span>
              <span style="font-family:monospace">&yen;{{ log.cost_yuan }}</span>
              <span class="text-muted">{{ log.latency_ms }}ms</span>
            </div>
          </div>
        </div>
        <div v-else class="text-muted text-center" style="padding:20px">{{ t('noData') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const stats = ref({
  total_users: '-',
  today_calls: '-',
  today_revenue_yuan: '-',
  active_suppliers: '-',
  top_models: [],
  recent_calls: [],
})

onMounted(async () => {
  try {
    stats.value = await api.getAdminDashboard()
  } catch (e) { /* keep defaults */ }
})
</script>
