<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">{{ t('userManagement') }}</n-h1>
      <n-button size="small" @click="loadUsers">{{ t('refresh') }}</n-button>
    </n-space>

    <!-- Stats -->
    <n-grid :x-gap="16" :cols="3" style="margin-bottom:24px">
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="t('totalUsers')" :value="totalUsers" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic label="活跃用户" :value="activeCount" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="true">
          <n-statistic :label="'已' + t('disableBtn')" :value="suspendedCount" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- User table -->
    <n-card :bordered="true">
      <n-data-table
        :columns="tableColumns"
        :data="users"
        :bordered="false"
        :single-line="false"
        :min-height="100"
      />
      <template v-if="hasMore" #footer>
        <n-space justify="center">
          <n-button size="small" :loading="loading" @click="loadMore">{{ t('loadMore') || '加载更多' }}</n-button>
        </n-space>
      </template>
    </n-card>

    <!-- Topup Modal -->
    <n-modal v-model:show="showTopup" preset="card" :title="'用户' + t('topUp')" style="max-width:400px" :bordered="true" :mask-closable="true">
      <n-space vertical :size="12">
        <n-text style="font-size:13px">{{ topupUser?.username }}</n-text>
        <n-text depth="3" style="font-size:11px">{{ topupUser?.email }}</n-text>
        <n-statistic label="当前余额" :value="'¥' + (topupUser?.balance_yuan || '0.00')" />
        <n-form-item label="充值金额 (元)">
          <n-input-number v-model:value="topupAmount" :min="0.01" :step="0.01" placeholder="0.00" style="width:100%" />
        </n-form-item>
        <n-alert v-if="topupError" type="error" :bordered="true" closable @close="topupError = ''">
          {{ topupError }}
        </n-alert>
        <n-button type="primary" style="width:100%" :loading="toppingUp" @click="doTopup">
          {{ toppingUp ? t('processingBtn') : t('confirmTopUp') }}
        </n-button>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useDialog } from 'naive-ui'
import {
  NCard, NDataTable, NGrid, NGridItem, NH1, NModal, NButton,
  NInputNumber, NSpace, NStatistic, NTag, NText, NFormItem, NAlert,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'

const { t } = useI18n()
const dialog = useDialog()

const users = ref([])
const hasMore = ref(false)
const cursor = ref(null)
const loading = ref(false)
const totalUsers = ref(0)

// Topup
const showTopup = ref(false)
const topupUser = ref(null)
const topupAmount = ref(0)
const topupError = ref('')
const toppingUp = ref(false)

const activeCount = computed(() => users.value.filter(u => u.status === 'active').length)
const suspendedCount = computed(() => users.value.filter(u => u.status !== 'active').length)

const tableColumns = [
  {
    title: t('user'),
    key: 'username',
    render: (row) => h('div', [
      h('div', { style: 'font-weight:600' }, row.username),
      h('div', { style: 'font-size:11px;color:var(--text-muted)' }, row.email),
    ]),
  },
  {
    title: t('role'),
    key: 'role',
    width: 100,
    render: (row) => {
      const type = row.role === 'super_admin' ? 'error' : row.role === 'admin' ? 'warning' : 'default'
      return h(NTag, { type, size: 'small' }, { default: () => row.role })
    },
  },
  {
    title: t('balance'),
    key: 'balance',
    width: 120,
    render: (row) => h('span', { style: 'font-weight:600;font-family:monospace' },
      '¥' + (row.balance_yuan != null ? row.balance_yuan : (row.balance / 100).toFixed(2))),
  },
  {
    title: t('status'),
    key: 'status',
    width: 80,
    render: (row) => h(NTag, {
      type: row.status === 'active' ? 'success' : 'error',
      size: 'small',
    }, { default: () => row.status === 'active' ? t('normalStatus') : t('suspended') }),
  },
  {
    title: t('createTime'),
    key: 'created_at',
    width: 120,
    render: (row) => formatDate(row.created_at),
  },
  {
    title: t('operation'),
    key: 'actions',
    width: 160,
    render: (row) => h('div', { style: 'display:flex;gap:4px' }, [
      h(NButton, { size: 'tiny', onClick: () => openTopup(row) }, { default: () => t('topUp') }),
      row.status === 'active'
        ? h(NButton, { size: 'tiny', color: '#dc2626', onClick: () => confirmToggle(row, 'suspend') },
            { default: () => t('disableBtn') })
        : h(NButton, { size: 'tiny', onClick: () => confirmToggle(row, 'activate') },
            { default: () => t('enableBtn') }),
    ]),
  },
]

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

function confirmToggle(u, action) {
  const label = action === 'suspend' ? '禁用' : '启用'
  dialog.warning({
    title: '确认操作',
    content: `确定${label}用户 "${u.username}"？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.toggleUser(u.id, action)
        u.status = action === 'suspend' ? 'suspended' : 'active'
      } catch (e) {
        dialog.error({ title: '操作失败', content: e.message })
      }
    },
  })
}

function openTopup(u) {
  topupUser.value = u
  topupAmount.value = 0
  topupError.value = ''
  showTopup.value = true
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
    showTopup.value = false
  } catch (e) {
    topupError.value = e.message || '充值失败'
  } finally {
    toppingUp.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(loadUsers)
</script>
