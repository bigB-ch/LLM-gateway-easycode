<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('adminUserDaily') }}</h1>
    </div>

    <div class="card card-padded mb-16" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
      <label style="font-size:12px">{{ t('date') }}：</label>
      <input type="date" v-model="dateFrom" class="form-input" style="width:auto;padding:4px 8px;font-size:12px" />
      <span style="color:var(--text-muted)">~</span>
      <input type="date" v-model="dateTo" class="form-input" style="width:auto;padding:4px 8px;font-size:12px" />
      <button class="btn btn-primary btn-xs" @click="search">{{ t('query') }}</button>
      <button class="btn btn-outline btn-xs" @click="resetFilter">{{ t('reset') }}</button>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('date') }}</th>
              <th>{{ t('user') }}</th>
              <th>{{ t('email') }}</th>
              <th>{{ t('model') }}</th>
              <th>{{ t('calls') }}</th>
              <th>{{ t('success') }}</th>
              <th>{{ t('inputToken') }}</th>
              <th>{{ t('outputToken') }}</th>
              <th>{{ t('cost') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!items.length">
              <td colspan="9">
                <div class="empty-state" style="padding:40px">
                  <div class="empty-state-icon">&#x1F4CA;</div>
                  <div class="empty-state-text">{{ t('noData') }}</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in items" :key="item.date + item.user_id + item.model">
              <td style="font-weight:500">{{ item.date }}</td>
              <td style="font-weight:600;font-size:13px">{{ item.username }}</td>
              <td class="text-muted" style="font-size:11px">{{ item.email }}</td>
              <td style="font-size:11px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="item.model">{{ item.model }}</td>
              <td style="font-family:monospace;font-size:12px">{{ (item.calls || 0).toLocaleString() }}</td>
              <td><span class="badge badge-success" style="font-size:10px">{{ item.success || 0 }}</span></td>
              <td style="font-family:monospace;font-size:12px">{{ (item.prompt_tokens || 0).toLocaleString() }}</td>
              <td style="font-family:monospace;font-size:12px">{{ (item.completion_tokens || 0).toLocaleString() }}</td>
              <td style="font-family:monospace;font-size:12px;color:var(--primary)">&yen;{{ item.cost_yuan || '0.00' }}</td>
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

const items = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const dateFrom = ref('')
const dateTo = ref('')

async function loadData() {
  try {
    const res = await api.getUserDaily(page.value, 20, dateFrom.value || undefined, dateTo.value || undefined)
    items.value = res.items || []
    total.value = res.total || 0
    totalPages.value = Math.max(1, Math.ceil(total.value / 20))
  } catch (e) { /* */ }
}

function goPage(p) {
  page.value = p
  loadData()
}

function search() {
  page.value = 1
  loadData()
}

function resetFilter() {
  dateFrom.value = ''
  dateTo.value = ''
  page.value = 1
  loadData()
}

onMounted(loadData)
</script>
