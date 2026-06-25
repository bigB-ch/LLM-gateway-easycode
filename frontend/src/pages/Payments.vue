<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">支付审核</n-h1>
      <n-button size="small" @click="loadPayments">{{ t('refresh') }}</n-button>
    </n-space>

    <!-- Payment Review Table -->
    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="payments" :bordered="false" :min-height="80" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  NCard, NDataTable, NH1, NButton, NSpace,
  NTag, NPopconfirm,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

const payments = ref([])

const tableColumns = [
  { title: '时间', key: 'created_at', render: (row) => h('span', { style: 'font-size:12px;white-space:nowrap' }, fmtTime(row.created_at)) },
  {
    title: '用户', key: 'user',
    render: (row) => h('div', [
      h('div', { style: 'font-weight:500' }, row.username),
      h('div', { style: 'font-size:11px;color:var(--text-muted)' }, row.email),
    ]),
  },
  { title: '金额', key: 'amount_yuan', render: (row) => h('span', { style: 'font-weight:700;color:var(--primary);font-size:15px' }, '¥' + row.amount_yuan) },
  {
    title: '方式', key: 'method',
    render: (row) => h(NTag, { type: row.method === 'alipay' ? 'primary' : 'success', size: 'small' },
      { default: () => row.method === 'alipay' ? '支付宝' : row.method === 'wechat' ? '微信' : row.method }),
  },
  { title: '状态', key: 'status', render: () => h(NTag, { type: 'warning', size: 'small' }, { default: () => '待审核' }) },
  {
    title: '操作', key: 'actions',
    render: (row) => h('div', { style: 'display:flex;gap:4px' }, [
      h(NPopconfirm, {
        onPositiveClick: () => verify(row.id, true),
      }, {
        trigger: () => h(NButton, { size: 'small', type: 'primary' }, { default: () => '通过' }),
        default: () => '确定通过这笔支付？',
      }),
      h(NPopconfirm, {
        onPositiveClick: () => verify(row.id, false),
      }, {
        trigger: () => h(NButton, { size: 'small', color: '#dc2626' }, { default: () => '拒绝' }),
        default: () => '确定拒绝这笔支付？',
      }),
    ]),
  },
]

onMounted(() => { loadPayments() })

async function loadPayments() {
  try { payments.value = (await api.getPendingPayments()).items || [] } catch (e) { /* */ }
}

async function verify(id, approved) {
  try { await api.verifyPayment(id, approved); loadPayments(); message.success(approved ? '已通过' : '已拒绝') }
  catch (e) { message.error('操作失败: ' + e.message) }
}

function fmtTime(iso) {
  return iso ? new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'
}
</script>
