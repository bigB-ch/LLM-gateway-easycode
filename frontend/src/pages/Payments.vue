<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">支付审核</n-h1>
      <n-button size="small" @click="loadPayments">{{ t('refresh') }}</n-button>
    </n-space>

    <!-- Fixed Payment QR Codes -->
    <n-card :bordered="true" style="margin-bottom:16px">
      <n-h3 style="margin:0 0 12px">固定收款码（手动审核模式）</n-h3>
      <n-text depth="2" style="font-size:12px;display:block;margin-bottom:12px">
        上传固定的支付宝/微信收款码图片链接。用户扫码付款后提交审核，管理员手动确认到账。
      </n-text>
      <n-space :size="16" wrap>
        <n-form-item label="支付宝收款码链接" style="flex:1;min-width:250px">
          <n-input v-model:value="alipayQrUrl" placeholder="https://..." />
        </n-form-item>
        <n-form-item label="微信收款码链接" style="flex:1;min-width:250px">
          <n-input v-model:value="wechatQrUrl" placeholder="https://..." />
        </n-form-item>
      </n-space>
      <n-text depth="3" style="font-size:11px;display:block;margin-bottom:12px">可将收款码上传到图床（如 imgse.com），粘贴图片链接即可</n-text>
      <n-button type="primary" size="small" :loading="savingQr" @click="saveQrConfig">{{ savingQr ? '保存中...' : '保存收款码' }}</n-button>
      <n-alert v-if="qrMsg" :type="qrMsg.includes('失败') ? 'error' : 'success'" :bordered="true" closable @close="qrMsg = ''" style="margin-top:8px;font-size:12px">
        {{ qrMsg }}
      </n-alert>
    </n-card>

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
  NCard, NDataTable, NH1, NH3, NButton, NInput, NSpace, NFormItem,
  NAlert, NTag, NPopconfirm,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

const payments = ref([])
const alipayQrUrl = ref('')
const wechatQrUrl = ref('')
const savingQr = ref(false)
const qrMsg = ref('')

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

onMounted(() => { loadPayments(); loadQrConfig() })

async function loadQrConfig() {
  try {
    const cfg = await api.getPaymentConfig()
    alipayQrUrl.value = cfg.alipay_qr_url || ''
    wechatQrUrl.value = cfg.wechat_qr_url || ''
  } catch (e) { /* */ }
}

async function saveQrConfig() {
  savingQr.value = true; qrMsg.value = ''
  try {
    await api.savePaymentConfig({ alipay_qr_url: alipayQrUrl.value, wechat_qr_url: wechatQrUrl.value })
    qrMsg.value = '保存成功'
  } catch (e) { qrMsg.value = '保存失败: ' + e.message }
  finally { savingQr.value = false }
}

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
