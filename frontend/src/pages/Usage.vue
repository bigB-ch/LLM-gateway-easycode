<template>
  <div>
    <!-- Top stat tags + compact toggle -->
    <div class="flex-between mb-16">
      <div style="display:flex;gap:12px">
        <div class="stat-tag stat-tag-blue">
          <span class="stat-tag-label">消耗额度</span>
          <span class="stat-tag-value">&yen;{{ totalCost }}</span>
        </div>
        <div class="stat-tag stat-tag-red">
          <span class="stat-tag-label">RPM</span>
          <span class="stat-tag-value">{{ rpm }}</span>
        </div>
        <div class="stat-tag stat-tag-white">
          <span class="stat-tag-label">TPM</span>
          <span class="stat-tag-value">{{ tpm }}</span>
        </div>
      </div>
      <button class="btn btn-outline btn-sm" @click="compactView = !compactView">
        {{ compactView ? t('defaultView') : t('compactList') }}
      </button>
    </div>

    <!-- Search & Filter bar -->
    <div class="card card-padded mb-16" style="padding:12px 16px">
      <div style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap">
        <div>
          <label class="form-label" style="font-size:11px">日期区间</label>
          <div style="display:flex;gap:6px">
            <input v-model="dateFrom" type="date" class="form-input" style="width:130px;padding:5px 8px;font-size:12px" />
            <span style="line-height:32px;color:var(--text-muted)">~</span>
            <input v-model="dateTo" type="date" class="form-input" style="width:130px;padding:5px 8px;font-size:12px" />
          </div>
        </div>
        <div>
          <label class="form-label" style="font-size:11px">令牌名称</label>
          <input v-model="filterKeyName" class="form-input" placeholder="搜索" style="width:110px;padding:5px 8px;font-size:12px" />
        </div>
        <div>
          <label class="form-label" style="font-size:11px">模型名称</label>
          <input v-model="filterModel" class="form-input" placeholder="搜索" style="width:110px;padding:5px 8px;font-size:12px" />
        </div>
        <div>
          <label class="form-label" style="font-size:11px">分组</label>
          <input v-model="filterGroup" class="form-input" placeholder="搜索" style="width:90px;padding:5px 8px;font-size:12px" />
        </div>
        <div>
          <label class="form-label" style="font-size:11px">Request ID</label>
          <input v-model="filterReqId" class="form-input" placeholder="搜索" style="width:140px;padding:5px 8px;font-size:12px" />
        </div>
        <div>
          <label class="form-label" style="font-size:11px">状态</label>
          <select v-model="filterStatus" class="form-select" style="width:80px;padding:5px 8px;font-size:12px">
            <option value="">{{ t('all') }}</option>
            <option value="success">{{ t('success') }}</option>
            <option value="error">{{ t('error') }}</option>
          </select>
        </div>
        <div style="display:flex;gap:6px;align-self:flex-end">
          <button class="btn btn-primary btn-sm" @click="doSearch">{{ t('query') }}</button>
          <button class="btn btn-outline btn-sm" @click="resetFilter">{{ t('reset') }}</button>
          <button class="btn btn-outline btn-sm">{{ t('columnSettings') }}</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card" v-if="filteredLogs.length">
      <div class="table-wrap" style="border:none;overflow-x:auto">
        <table class="data-table" :style="{fontSize: compactView ? '12px' : '13px'}">
          <thead>
            <tr>
              <th style="min-width:140px">时间</th>
              <th style="min-width:80px">令牌</th>
              <th style="width:60px">分组</th>
              <th style="width:90px">类型</th>
              <th style="min-width:100px">模型</th>
              <th style="width:80px">用时/首字</th>
              <th style="width:70px">输入</th>
              <th style="width:70px">输出</th>
              <th style="width:80px">花费</th>
              <th style="width:100px">IP</th>
              <th style="width:60px">详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in filteredLogs" :key="log.id">
              <td class="text-secondary" style="font-size:12px">{{ fmtTime(log.created_at) }}</td>
              <td><span class="key-masked" style="font-size:12px">{{ log.key_name || '默认' }}</span></td>
              <td class="text-secondary" style="font-size:12px">{{ log.group || '-' }}</td>
              <td><span class="badge badge-primary" style="font-size:10px">{{ log.type || 'chat' }}</span></td>
              <td><span class="inline-code" style="font-size:11px">{{ log.model }}</span></td>
              <td class="text-secondary" style="font-size:12px">{{ log.duration_ms || '-' }}ms</td>
              <td style="font-size:12px">{{ log.prompt_tokens || 0 }}</td>
              <td style="font-size:12px">{{ log.completion_tokens || 0 }}</td>
              <td style="font-size:12px;font-weight:500">&yen;{{ log.cost_yuan || '0.00' }}</td>
              <td class="text-muted" style="font-size:11px">{{ log.ip || '-' }}</td>
              <td>
                <button class="btn btn-outline btn-xs" @click="showDetail(log)">详情</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div style="display:flex;justify-content:center;gap:8px;padding:12px">
        <button class="btn btn-outline btn-sm" v-if="page > 1" @click="loadPage(page - 1)">{{ t('prevPage') }}</button>
        <button class="btn btn-outline btn-sm" @click="loadPage(page + 1)">{{ t('nextPage') }}</button>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="card card-padded">
      <div class="empty-state">
        <div class="empty-state-icon">&#x1F50D;</div>
        <div class="empty-state-text">搜索无结果</div>
        <div class="empty-state-sub">{{ hasFilter ? t('adjustFilterHint') : t('noUsageData') }}</div>
      </div>
    </div>

    <!-- Detail modal -->
    <div v-if="detailLog" class="modal-overlay" @click.self="detailLog = null">
      <div class="modal-card">
        <div class="flex-between mb-16">
          <h3 class="section-title">调用详情</h3>
          <button class="btn btn-outline btn-xs" @click="detailLog = null">&#x2715;</button>
        </div>
        <div class="text-secondary" style="font-size:12px;line-height:1.8">
          <div>Request ID: <code>{{ detailLog.id }}</code></div>
          <div>模型: {{ detailLog.model }}</div>
          <div>时间: {{ fmtTime(detailLog.created_at) }}</div>
          <div>耗时: {{ detailLog.duration_ms || '-' }}ms</div>
          <div>Tokens: {{ detailLog.prompt_tokens }} in / {{ detailLog.completion_tokens }} out</div>
          <div>花费: &yen;{{ detailLog.cost_yuan || '0.00' }}</div>
          <div>IP: {{ detailLog.ip || '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const logs = ref([])
const page = ref(1)
const compactView = ref(false)
const detailLog = ref(null)

// Filters
const dateFrom = ref('')
const dateTo = ref('')
const filterKeyName = ref('')
const filterModel = ref('')
const filterGroup = ref('')
const filterReqId = ref('')
const filterStatus = ref('')

const totalCost = ref('0.00')
const rpm = ref(0)
const tpm = ref(0)

const hasFilter = computed(() =>
  dateFrom.value || dateTo.value || filterKeyName.value || filterModel.value ||
  filterGroup.value || filterReqId.value || filterStatus.value
)

const filteredLogs = computed(() => {
  let list = logs.value
  if (filterKeyName.value) list = list.filter(l => (l.key_name || '').includes(filterKeyName.value))
  if (filterModel.value) list = list.filter(l => l.model.includes(filterModel.value))
  if (filterGroup.value) list = list.filter(l => (l.group || '').includes(filterGroup.value))
  if (filterReqId.value) list = list.filter(l => l.id.includes(filterReqId.value))
  if (filterStatus.value) list = list.filter(l => l.status === filterStatus.value)
  return list
})

function fmtTime(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(() => loadPage(1))

async function loadPage(p) {
  page.value = p
  try {
    const data = await api.getUsage(p, dateFrom.value || null, dateTo.value || null)
    logs.value = data.items || []
    totalCost.value = data.total_cost_yuan || '0.00'
    rpm.value = '-'
    tpm.value = '-'
  } catch (e) { /* */ }
}

function doSearch() { loadPage(1) }
function resetFilter() {
  dateFrom.value = ''; dateTo.value = ''; filterKeyName.value = ''
  filterModel.value = ''; filterGroup.value = ''; filterReqId.value = ''
  filterStatus.value = ''
  loadPage(1)
}

function showDetail(log) { detailLog.value = log }
</script>

<style scoped>
.stat-tag {
  padding: 8px 20px;
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 120px;
}
.stat-tag-blue { background: var(--primary-light); }
.stat-tag-red { background: #fef2f2; }
.stat-tag-white { background: #f5f5f5; border: 1px solid var(--border); }

.stat-tag-label { font-size: 11px; color: var(--text-muted); }
.stat-tag-blue .stat-tag-label { color: var(--primary); }
.stat-tag-red .stat-tag-label { color: var(--danger); }
.stat-tag-value { font-size: 20px; font-weight: 700; color: var(--text); }

.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  z-index: 300;
}
.modal-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}
</style>
