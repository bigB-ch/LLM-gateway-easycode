<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('userManagement') }}</h1>
      <button class="btn btn-outline btn-sm" @click="loadUsers">{{ t('refresh') }}</button>
    </div>

    <!-- Stats bar -->
    <div class="stat-grid mb-24" style="grid-template-columns:repeat(3,1fr)">
      <div class="stat-card mc-blue">
        <div class="stat-icon">&#x1F465;</div>
        <div class="stat-body">
          <div class="stat-value">{{ totalUsers }}</div>
          <div class="stat-label">{{ t('totalUsers') }}</div>
        </div>
      </div>
      <div class="stat-card mc-mint">
        <div class="stat-icon">&#x2705;</div>
        <div class="stat-body">
          <div class="stat-value">{{ activeCount }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </div>
      <div class="stat-card mc-yellow">
        <div class="stat-icon">&#x1F6AB;</div>
        <div class="stat-body">
          <div class="stat-value">{{ suspendedCount }}</div>
          <div class="stat-label">已{{ t('disableBtn') }}</div>
        </div>
      </div>
    </div>

    <!-- User table -->
    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('user') }}</th>
              <th>{{ t('role') }}</th>
              <th>{{ t('balance') }}</th>
              <th>{{ t('status') }}</th>
              <th>{{ t('createTime') }}</th>
              <th>{{ t('operation') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="users.length === 0">
              <td colspan="6">
                <div class="empty-state" style="padding:40px">
                  <div class="empty-state-icon">&#x1F465;</div>
                  <div class="empty-state-text">{{ t('noData') }}</div>
                </div>
              </td>
            </tr>
            <tr v-for="u in users" :key="u.id">
              <td>
                <div style="font-weight:600">{{ u.username }}</div>
                <div class="text-muted" style="font-size:11px">{{ u.email }}</div>
              </td>
              <td>
                <span :class="'badge ' + (u.role === 'super_admin' ? 'badge-danger' : u.role === 'admin' ? 'badge-warning' : 'badge-default')" style="font-size:10px">{{ u.role }}</span>
              </td>
              <td style="font-weight:600;font-family:monospace">&yen;{{ u.balance_yuan != null ? u.balance_yuan : (u.balance / 100).toFixed(2) }}</td>
              <td>
                <span :class="'badge ' + (u.status === 'active' ? 'badge-success' : 'badge-danger')" style="font-size:10px">{{ u.status === 'active' ? t('normalStatus') : t('suspended') }}</span>
              </td>
              <td class="text-muted" style="font-size:12px">{{ formatDate(u.created_at) }}</td>
              <td>
                <button class="btn btn-outline btn-xs" @click="openTopup(u)" style="margin-right:4px">{{ t('topUp') }}</button>
                <button v-if="u.status === 'active'" class="btn btn-danger btn-xs" @click="toggleUser(u, 'suspend')">{{ t('disableBtn') }}</button>
                <button v-else class="btn btn-outline btn-xs" @click="toggleUser(u, 'activate')">{{ t('enableBtn') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="hasMore" class="card-padded text-center">
        <button class="btn btn-outline btn-sm" @click="loadMore" :disabled="loading">加载更多</button>
      </div>
    </div>

    <!-- Topup Modal -->
    <div v-if="topupUser" class="modal-overlay" @click.self="topupUser = null">
      <div class="modal-content" style="max-width:400px">
        <div class="modal-header flex-between">
          <h3>用户{{ t('topUp') }}</h3>
          <button class="btn btn-outline btn-xs" @click="topupUser = null">&times;</button>
        </div>
        <div class="modal-body">
          <div style="margin-bottom:12px">
            <span style="font-size:13px">{{ topupUser.username }}</span>
            <span class="text-muted" style="font-size:11px;margin-left:8px">{{ topupUser.email }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">{{ t('currentBalance') }}</label>
            <div style="font-weight:600;font-size:16px">&yen;{{ topupUser.balance_yuan }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ t('topUp') }}金额 (元)</label>
            <input v-model.number="topupAmount" type="number" step="0.01" min="0.01" class="form-input" placeholder="0.00" />
          </div>
          <div v-if="topupError" class="alert alert-error" style="font-size:12px">{{ topupError }}</div>
          <button class="btn btn-primary" style="width:100%" :disabled="toppingUp" @click="doTopup">
            {{ toppingUp ? t('processingBtn') : t('confirmTopUp') }}
          </button>
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

const users = ref([])
const hasMore = ref(false)
const cursor = ref(null)
const loading = ref(false)
const totalUsers = ref(0)

// Topup
const topupUser = ref(null)
const topupAmount = ref(0)
const topupError = ref('')
const toppingUp = ref(false)

const activeCount = computed(() => users.value.filter(u => u.status === 'active').length)
const suspendedCount = computed(() => users.value.filter(u => u.status !== 'active').length)

async function loadUsers() {
  loading.value = true
  try {
    const res = await api.listUsers(null, 50)
    users.value = res.items || []
    hasMore.value = res.has_more || false
    cursor.value = res.next_cursor || null
    totalUsers.value = (res.items || []).length
  } catch (e) { /* */ }
  finally { loading.value = false }
}

async function loadMore() {
  if (!cursor.value) return
  loading.value = true
  try {
    const res = await api.listUsers(cursor.value, 50)
    users.value = [...users.value, ...(res.items || [])]
    hasMore.value = res.has_more || false
    cursor.value = res.next_cursor || null
  } catch (e) { /* */ }
  finally { loading.value = false }
}

async function toggleUser(u, action) {
  const label = action === 'suspend' ? '禁用' : '启用'
  if (!confirm(`确定${label}用户 "${u.username}"？`)) return
  try {
    await api.toggleUser(u.id, action)
    u.status = action === 'suspend' ? 'suspended' : 'active'
  } catch (e) { alert('操作失败: ' + e.message) }
}

function openTopup(u) {
  topupUser.value = u
  topupAmount.value = 0
  topupError.value = ''
}

async function doTopup() {
  if (!topupAmount.value || topupAmount.value <= 0) {
    topupError.value = '请输入有效金额'
    return
  }
  toppingUp.value = true
  topupError.value = ''
  try {
    const res = await api.topupUser(topupUser.value.id, topupAmount.value)
    topupUser.value.balance_yuan = res.balance_yuan
    const u = users.value.find(x => x.id === topupUser.value.id)
    if (u) u.balance_yuan = res.balance_yuan
    topupUser.value = null
  } catch (e) {
    topupError.value = e.message || '充值失败'
  } finally {
    toppingUp.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit' })
}

onMounted(loadUsers)
</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
}
.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}
.modal-body {
  padding: 20px;
}
</style>
