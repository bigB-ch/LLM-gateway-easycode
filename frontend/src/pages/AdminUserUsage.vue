<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('adminUserUsage') }}</h1>
    </div>

    <!-- All users usage summary table -->
    <div class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('user') }}</th>
              <th>{{ t('email') }}</th>
              <th>{{ t('totalCalls') }}</th>
              <th>{{ t('success') }}</th>
              <th>{{ t('inputToken') }}</th>
              <th>{{ t('outputToken') }}</th>
              <th>{{ t('totalCost') }}</th>
              <th>{{ t('lastUsed') }}</th>
              <th>{{ t('operation') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="9" style="text-align:center;padding:40px">
                加载中...
              </td>
            </tr>
            <tr v-else-if="items.length === 0">
              <td colspan="9">
                <div class="empty-state" style="padding:30px">
                  <div class="empty-state-icon">&#x1F4CA;</div>
                  <div class="empty-state-text">{{ t('noData') }}</div>
                </div>
              </td>
            </tr>
            <tr v-for="row in items" :key="row.user_id">
              <td style="font-weight:500">{{ row.username }}</td>
              <td class="text-muted" style="font-size:12px">{{ row.email }}</td>
              <td style="font-family:monospace">{{ row.calls.toLocaleString() }}</td>
              <td><span class="badge badge-success" style="font-size:10px">{{ row.success }}</span></td>
              <td style="font-family:monospace">{{ row.prompt_tokens.toLocaleString() }}</td>
              <td style="font-family:monospace">{{ row.completion_tokens.toLocaleString() }}</td>
              <td style="font-family:monospace;color:var(--primary)">&yen;{{ row.cost_yuan }}</td>
              <td class="text-muted" style="font-size:11px">{{ formatTime(row.last_used) }}</td>
              <td>
                <button class="btn btn-outline btn-xs" @click="openDetail(row)">{{ t('details') }}</button>
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

    <!-- Per-model detail modal -->
    <div v-if="detailUser" class="modal-overlay" @click.self="closeDetail">
      <div class="modal" style="max-width:800px">
        <div class="modal-header">
          <h3>{{ t('perModelUsage') }} - {{ detailUser.username }}</h3>
          <button class="modal-close" @click="closeDetail">&times;</button>
        </div>
        <div class="modal-body" style="max-height:70vh;overflow-y:auto">
          <!-- Model summary -->
          <h4 style="margin:0 0 8px;font-size:13px;color:var(--text-muted)">{{ t('modelSummary') }}</h4>
          <table class="data-table" style="margin-bottom:16px">
            <thead>
              <tr>
                <th>{{ t('model') }}</th>
                <th>{{ t('calls') }}</th>
                <th>{{ t('success') }}</th>
                <th>{{ t('inputToken') }}</th>
                <th>{{ t('outputToken') }}</th>
                <th>{{ t('totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="detailModels.length === 0">
                <td colspan="6" style="text-align:center;padding:20px">
                  加载中...
                </td>
              </tr>
              <tr v-for="m in detailModels" :key="m.model">
                <td style="font-weight:500;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="m.model">{{ m.model }}</td>
                <td style="font-family:monospace">{{ m.calls.toLocaleString() }}</td>
                <td><span class="badge badge-success" style="font-size:10px">{{ m.success }}</span></td>
                <td style="font-family:monospace">{{ m.prompt_tokens.toLocaleString() }}</td>
                <td style="font-family:monospace">{{ m.completion_tokens.toLocaleString() }}</td>
                <td style="font-family:monospace;color:var(--primary)">&yen;{{ m.cost_yuan }}</td>
              </tr>
            </tbody>
          </table>

          <!-- Detail logs -->
          <h4 style="margin:0 0 8px;font-size:13px;color:var(--text-muted)">{{ t('usageLogs') }}</h4>
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
              <tr v-if="detailLogs.length === 0">
                <td colspan="8" style="text-align:center;padding:20px">
                  加载中...
                </td>
              </tr>
              <tr v-for="log in detailLogs" :key="log.id">
                <td class="text-muted" style="font-size:11px;white-space:nowrap">{{ formatTime(log.created_at) }}</td>
                <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500;font-size:13px" :title="log.model">{{ log.model }}</td>
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

          <!-- Pagination for detail logs -->
          <div v-if="detailTotalPages > 1" class="flex-between" style="padding:12px 0">
            <span class="text-muted" style="font-size:12px">{{ t('totalRecords', { n: detailTotal }) }}</span>
            <div style="display:flex;gap:4px">
              <button class="btn btn-outline btn-xs" :disabled="detailPage <= 1" @click="detailGoPage(detailPage - 1)">{{ t('prevPage') }}</button>
              <span class="text-muted" style="font-size:12px;padding:4px 8px">{{ detailPage }} / {{ detailTotalPages }}</span>
              <button class="btn btn-outline btn-xs" :disabled="detailPage >= detailTotalPages" @click="detailGoPage(detailPage + 1)">{{ t('nextPage') }}</button>
            </div>
          </div>
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

const items = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const loading = ref(true)

// Detail modal state
const detailUser = ref(null)
const detailModels = ref([])
const detailLogs = ref([])
const detailPage = ref(1)
const detailTotal = ref(0)
const detailTotalPages = ref(1)

async function loadData() {
  loading.value = true
  try {
    const res = await api.getUserUsageSummary(page.value, 20)
    items.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
  loading.value = false
}

function goPage(p) {
  page.value = p
  loadData()
}

async function openDetail(row) {
  detailUser.value = row
  detailPage.value = 1
  await loadDetail()
}

function closeDetail() {
  detailUser.value = null
  detailModels.value = []
  detailLogs.value = []
}

async function loadDetail() {
  if (!detailUser.value) return
  try {
    const res = await api.getUserModelUsage(detailUser.value.user_id, detailPage.value, 20)
    detailModels.value = res.models || []
    detailLogs.value = res.logs || []
    detailTotal.value = res.total || 0
    detailTotalPages.value = Math.max(1, Math.ceil(detailTotal.value / 20))
  } catch (e) { /* */ }
}

function detailGoPage(p) {
  detailPage.value = p
  loadDetail()
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

onMounted(loadData)
</script>
