<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('globalUsageLog') }}</h1>
      <button class="btn btn-outline btn-sm" @click="loadUsage">{{ t('refresh') }}</button>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('time') }}</th>
              <th>{{ t('model') }}</th>
              <th>{{ t('supplier') }}</th>
              <th>{{ t('inputToken') }}</th>
              <th>{{ t('outputToken') }}</th>
              <th>{{ t('cost') }}</th>
              <th>{{ t('duration') }}</th>
              <th>{{ t('status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="logs.length === 0">
              <td colspan="8">
                <div class="empty-state" style="padding:40px">
                  <div class="empty-state-icon">&#x1F4CA;</div>
                  <div class="empty-state-text">{{ t('noData') }}</div>
                </div>
              </td>
            </tr>
            <tr v-for="log in logs" :key="log.id">
              <td class="text-muted" style="font-size:11px;white-space:nowrap">{{ formatTime(log.created_at) }}</td>
              <td style="font-weight:500;font-size:13px">{{ log.model }}</td>
              <td style="font-size:12px">{{ log.provider }}</td>
              <td style="font-family:monospace;font-size:12px">{{ log.prompt_tokens?.toLocaleString() }}</td>
              <td style="font-family:monospace;font-size:12px">{{ log.completion_tokens?.toLocaleString() }}</td>
              <td style="font-family:monospace;font-size:12px;color:var(--primary)">&yen;{{ log.cost_yuan }}</td>
              <td style="font-size:12px">{{ log.latency_ms }}ms</td>
              <td>
                <span :class="'badge ' + (log.status === 'success' ? 'badge-success' : 'badge-danger')" style="font-size:9px">
                  {{ log.status === 'success' ? t('success') : t('error') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="totalPages > 1" class="card-padded flex-between">
        <span class="text-muted" style="font-size:12px">{{ t('totalRecords', { n: total }) }}</span>
        <div style="display:flex;gap:4px">
          <button class="btn btn-outline btn-xs" :disabled="page <= 1" @click="goPage(page - 1)">{{ t('prevPage') }}</button>
          <span class="text-muted" style="font-size:12px;padding:4px 8px">{{ page }} / {{ totalPages }}</span>
          <button class="btn btn-outline btn-xs" :disabled="page >= totalPages" @click="goPage(page + 1)">{{ t('nextPage') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const logs = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)

async function loadUsage() {
  try {
    const res = await api.getAllUsage(page.value, 20)
    logs.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
}
onMounted(loadUsage)

function goPage(p) {
  page.value = p
  loadUsage()
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'
  })
}
</script>
