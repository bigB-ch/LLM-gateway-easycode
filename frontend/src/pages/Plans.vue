<template>
  <div>
    <n-space :size="16" style="margin-bottom:16px">
      <!-- Left: Recharge -->
      <n-card :bordered="true" style="flex:1">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <n-text style="font-size:14px;font-weight:600">{{ t('accountTopUp') }}</n-text>
              <n-space :size="24" style="margin-top:10px">
                <div><n-text style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65">{{ t('currentBalance') }}</n-text><n-text style="font-size:22px;font-weight:700;display:block">&yen;{{ balance }}</n-text></div>
                <div><n-text style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65">{{ t('totalSpent') }}</n-text><n-text style="font-size:22px;font-weight:700;display:block">&yen;{{ totalCost }}</n-text></div>
                <div><n-text style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65">{{ t('requestCount') }}</n-text><n-text style="font-size:22px;font-weight:700;display:block">{{ totalCalls }}</n-text></div>
              </n-space>
            </div>
          </div>
        </template>

        <n-h3 style="margin:0 0 12px">{{ t('customTopUp') }}</n-h3>
        <n-space align="flex-end" wrap :size="10" style="margin-bottom:20px">
          <n-form-item :label="t('topUpUnits')" style="max-width:200px">
            <n-input-number v-model:value="customAmount" :min="1" style="width:100%" />
          </n-form-item>
          <n-form-item :label="t('payMethod')" style="max-width:140px">
            <n-select v-model:value="payMethod" :options="[{label:'支付宝',value:'alipay'},{label:'微信支付',value:'wechat'}]" />
          </n-form-item>
          <div>
            <n-text style="font-size:12px;display:block">{{ t('actualPay') }}</n-text>
            <n-text style="font-weight:700;font-size:20px;color:var(--primary)">&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</n-text>
          </div>
          <n-button type="primary" :disabled="!customAmount" @click="startPayment">{{ t('topUpBtn') }}</n-button>
        </n-space>

        <n-h3 style="margin:0 0 12px">{{ t('quickTiers') }}</n-h3>
        <n-grid :x-gap="10" :y-gap="10" :cols="4">
          <n-grid-item v-for="p in quickPlans" :key="p.cny">
            <div :style="{ padding:'12px 8px',textAlign:'center',border:'1px solid ' + (customAmount === Math.round(p.cny / pricePerUnit) ? 'var(--primary)' : 'var(--border)'),borderRadius:'var(--radius-sm)',cursor:'pointer',background: customAmount === Math.round(p.cny / pricePerUnit) ? 'var(--primary-light)' : '#fff' }" @click="customAmount = Math.round(p.cny / pricePerUnit)">
              <n-text style="font-weight:700;font-size:16px">&yen;{{ p.cny }}</n-text>
            </div>
          </n-grid-item>
        </n-grid>

        <n-divider />
        <n-space align="center" :size="8" style="margin-bottom:12px">
          <n-h3 style="margin:0">{{ t('redeemCodeTitle') }}</n-h3>
          <n-tag size="small" type="warning">功能改进中，敬请期待</n-tag>
        </n-space>
        <n-space :size="10">
          <n-input v-model:value="redeemCode" :placeholder="t('redeemPlaceholder')" disabled style="max-width:280px;opacity:0.5" />
          <n-button disabled style="opacity:0.5">{{ t('redeemBtn') }}</n-button>
        </n-space>
      </n-card>

      <!-- Right: Recharge History -->
      <n-card :bordered="true" style="flex:1">
        <template #header>
          <div>
            <n-text style="font-size:14px;font-weight:600">{{ t('rechargeHistoryTitle') }}</n-text>
            <n-space :size="24" style="margin-top:10px">
              <div><n-text style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65">{{ t('totalRecharged') }}</n-text><n-text style="font-size:22px;font-weight:700;display:block">&yen;{{ totalRecharged }}</n-text></div>
            </n-space>
          </div>
        </template>
        <div v-if="rechargeHistory.length" style="max-height:360px;overflow-y:auto">
          <div v-for="r in rechargeHistory" :key="r.id" class="flex-between" style="padding:10px 0;border-bottom:1px solid var(--border-light);font-size:13px">
            <div>
              <n-text style="font-weight:500">
                {{ r.method === 'redeem' ? t('redeemRecharge') : r.method === 'alipay' ? t('alipay') : r.method === 'wechat' ? t('wechatPay') : t('balanceRecharge') }}
                <n-tag v-if="r.status === 'pending'" type="warning" size="tiny" style="margin-left:4px">待审核</n-tag>
                <n-tag v-else-if="r.status === 'success'" type="success" size="tiny" style="margin-left:4px">已到账</n-tag>
              </n-text>
              <n-text depth="3" style="font-size:11px;display:block">{{ fmtTime(r.created_at) }}</n-text>
            </div>
            <n-text :style="{fontWeight:'700',color:r.status==='success'?'var(--success)':'var(--text-secondary)'}">+&yen;{{ (r.amount / 100).toFixed(2) }}</n-text>
          </div>
        </div>
        <n-empty v-else :description="t('noRechargeHistory')" style="padding:32px 0" />
      </n-card>
    </n-space>

    <!-- Payment Modal -->
    <n-modal v-model:show="showPayment" preset="card" :title="payMethod === 'alipay' ? '支付宝扫码支付' : '微信扫码支付'" style="max-width:420px" :bordered="true">
      <div style="text-align:center">
        <n-text style="font-size:24px;font-weight:700;color:var(--primary);display:block;margin-bottom:16px">&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</n-text>

        <div v-if="fixedQrCode" style="margin-bottom:16px">
          <img :src="fixedQrCode" alt="QR Code" style="max-width:220px;border:1px solid var(--border-light);border-radius:8px" />
          <n-text style="font-size:14px;font-weight:600;display:block;margin-top:8px">请扫码转账 {{ (customAmount * pricePerUnit).toFixed(2) }} 元</n-text>
        </div>
        <n-spin v-else-if="paymentLoading" style="padding:20px 0;margin-bottom:16px" />
        <n-alert v-if="paymentError" type="error" :bordered="true" style="font-size:12px;margin-bottom:8px">{{ paymentError }}</n-alert>
        <n-alert v-if="paymentSuccess" type="success" :bordered="true" style="font-size:12px;margin-bottom:8px">{{ paymentSuccess }}</n-alert>

        <n-button v-if="fixedQrCode && !paymentSuccess" type="primary" size="small" style="width:100%;margin-bottom:8px" :loading="submittingPayment" @click="submitManualPayment">
          {{ submittingPayment ? '提交中...' : '我已支付，通知管理员' }}
        </n-button>
        <n-text v-if="fixedQrCode" depth="3" style="font-size:12px;display:block">付款后请点击上方按钮，管理员审核后到账</n-text>
      </div>
    </n-modal>

    <n-text depth="3" style="text-align:center;display:block;padding:16px 0;font-size:12px">&copy;2026 EasyCode {{ t('copyright') }}</n-text>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  NCard, NButton, NDivider, NEmpty, NFormItem, NGrid, NGridItem, NH3,
  NInput, NInputNumber, NModal, NSelect, NSpace, NSpin, NTag, NText, NAlert,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()
const message = useMessage()

const balance = ref('0.00'); const totalCost = ref('0.00'); const totalCalls = ref(0)
const customAmount = ref(1); const payMethod = ref('alipay'); const redeemCode = ref('')
const rechargeHistory = ref([]); const totalRecharged = ref('0.00')
const pricePerUnit = 1
const quickPlans = [{ cny: 10 }, { cny: 50 }, { cny: 100 }, { cny: 200 }, { cny: 500 }, { cny: 1000 }, { cny: 2000 }, { cny: 5000 }]

const showPayment = ref(false)
const fixedQrCode = ref('')
const paymentLoading = ref(false)
const paymentError = ref('')
const paymentSuccess = ref('')
const submittingPayment = ref(false)
const cachedPaymentConfig = ref({})

onMounted(async () => {
  try { const d = await api.getDashboard(); totalCalls.value = d.total_calls || 0; totalCost.value = (d.total_cost_yuan || 0).toFixed(2) } catch (e) { /* */ }
  try { const u = await api.getMe(); balance.value = ((u.balance || 0) / 100).toFixed(2) } catch (e) { /* */ }
  loadRechargeHistory()
  loadPaymentConfig()
})

async function loadPaymentConfig() {
  try { const cfg = await api.getPaymentConfig(); cachedPaymentConfig.value = cfg } catch (e) { /* */ }
}

async function loadRechargeHistory() {
  try {
    const res = await api.getRechargeHistory()
    rechargeHistory.value = res.items || []
    totalRecharged.value = (rechargeHistory.value.filter(r => r.status === 'success').reduce((s, r) => s + r.amount, 0) / 100).toFixed(2)
  } catch (e) { /* */ }
}

async function startPayment() {
  if (!customAmount.value) return
  showPayment.value = true
  fixedQrCode.value = ''
  paymentError.value = ''
  paymentSuccess.value = ''
  paymentLoading.value = true

  const cfg = cachedPaymentConfig.value || {}
  const qrUrl = payMethod.value === 'alipay' ? cfg.alipay_qr_url : cfg.wechat_qr_url
  if (qrUrl) {
    fixedQrCode.value = qrUrl
    paymentLoading.value = false
    return
  }

  const amount = customAmount.value * pricePerUnit
  try {
    const res = await api.alipayRecharge(amount)
    fixedQrCode.value = res.qr_code
  } catch (e) {
    paymentError.value = '暂未配置收款码，请联系管理员'
  } finally {
    paymentLoading.value = false
  }
}

async function submitManualPayment() {
  const amount = customAmount.value * pricePerUnit
  submittingPayment.value = true
  try {
    await api.recharge(amount, payMethod.value)
    paymentSuccess.value = '已提交，等待管理员审核'
    setTimeout(() => { showPayment.value = false; customAmount.value = 1; loadRechargeHistory() }, 2000)
  } catch (e) {
    paymentError.value = '提交失败: ' + e.message
  } finally { submittingPayment.value = false }
}

function fmtTime(iso) { return iso ? new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-' }
</script>
