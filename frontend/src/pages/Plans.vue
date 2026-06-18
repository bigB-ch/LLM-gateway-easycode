<template>
  <div>
    <div style="display:flex;gap:16px;margin-bottom:16px">
      <!-- Left: Recharge -->
      <div class="card" style="flex:1">
        <div class="wallet-header wallet-header-blue">
          <div>
            <div class="wallet-header-title">{{ t('accountTopUp') }}</div>
            <div style="display:flex;gap:24px;margin-top:10px">
              <div><div class="wallet-stat-label">{{ t('currentBalance') }}</div><div class="wallet-stat-value">&yen;{{ balance }}</div></div>
              <div><div class="wallet-stat-label">{{ t('totalSpent') }}</div><div class="wallet-stat-value">&yen;{{ totalCost }}</div></div>
              <div><div class="wallet-stat-label">{{ t('requestCount') }}</div><div class="wallet-stat-value">{{ totalCalls }}</div></div>
            </div>
          </div>
        </div>
        <div class="card-padded">
          <h3 class="section-title mb-12">{{ t('customTopUp') }}</h3>
          <div style="display:flex;gap:10px;align-items:flex-end;margin-bottom:20px;flex-wrap:wrap">
            <div style="flex:1;max-width:200px">
              <label class="form-label">{{ t('topUpUnits') }}</label>
              <input v-model.number="customAmount" type="number" min="1" class="form-input" :placeholder="t('topUpUnits')" />
            </div>
            <div style="flex:1;max-width:140px">
              <label class="form-label">{{ t('payMethod') }}</label>
              <select v-model="payMethod" class="form-select">
                <option value="alipay">支付宝</option>
                <option value="wechat">微信支付</option>
              </select>
            </div>
            <div>
              <label class="form-label">{{ t('actualPay') }}</label>
              <div style="font-weight:700;font-size:20px;color:var(--primary)">&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</div>
            </div>
            <button class="btn btn-primary" @click="startPayment" :disabled="!customAmount">
              {{ t('topUpBtn') }}
            </button>
          </div>

          <h3 class="section-title mb-12">{{ t('quickTiers') }}</h3>
          <div class="quick-amounts">
            <div v-for="p in quickPlans" :key="p.cny" :class="'quick-amount-card ' + (customAmount === Math.round(p.cny / pricePerUnit) ? 'active' : '')" @click="customAmount = Math.round(p.cny / pricePerUnit)">
              <div style="font-weight:700;font-size:16px">&yen;{{ p.cny }}</div>
            </div>
          </div>

          <div style="margin-top:20px;padding-top:20px;border-top:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
              <h3 class="section-title mb-0">{{ t('redeemCodeTitle') }}</h3>
              <span style="font-size:11px;color:#d97706;background:#fef3c7;padding:2px 8px;border-radius:4px">功能改进中，敬请期待</span>
            </div>
            <div style="display:flex;gap:10px">
              <input v-model="redeemCode" class="form-input" :placeholder="t('redeemPlaceholder')" style="flex:1;max-width:280px;opacity:0.5" disabled />
              <button class="btn btn-outline" disabled style="opacity:0.5">
                {{ t('redeemBtn') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Recharge History -->
      <div class="card" style="flex:1">
        <div class="wallet-header wallet-header-green">
          <div>
            <div class="wallet-header-title">{{ t('rechargeHistoryTitle') }}</div>
            <div style="display:flex;gap:24px;margin-top:10px">
              <div><div class="wallet-stat-label">{{ t('totalRecharged') }}</div><div class="wallet-stat-value">&yen;{{ totalRecharged }}</div></div>
            </div>
          </div>
        </div>
        <div class="card-padded">
          <div v-if="rechargeHistory.length" style="max-height:360px;overflow-y:auto">
            <div v-for="r in rechargeHistory" :key="r.id" style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border-light);font-size:13px">
              <div>
                <div style="font-weight:500">
                  {{ r.method === 'redeem' ? t('redeemRecharge') : r.method === 'alipay' ? t('alipay') : r.method === 'wechat' ? t('wechatPay') : t('balanceRecharge') }}
                  <span v-if="r.status === 'pending'" class="badge badge-warning" style="font-size:9px;margin-left:4px">待审核</span>
                  <span v-else-if="r.status === 'success'" class="badge badge-success" style="font-size:9px;margin-left:4px">已到账</span>
                </div>
                <div class="text-muted" style="font-size:11px">{{ fmtTime(r.created_at) }}</div>
              </div>
              <div :style="{fontWeight:'700',color:r.status==='success'?'var(--success)':'var(--text-secondary)'}">+&yen;{{ (r.amount / 100).toFixed(2) }}</div>
            </div>
          </div>
          <div v-else class="empty-state" style="padding:32px 0">
            <div class="empty-state-icon" style="font-size:32px">&#x1F4B0;</div>
            <div class="empty-state-text" style="font-size:13px">{{ t('noRechargeHistory') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <div v-if="showPayment" class="modal-overlay" @click.self="showPayment = false">
      <div class="modal-content" style="max-width:420px">
        <div class="modal-header flex-between">
          <h3>{{ payMethod === 'alipay' ? '支付宝扫码支付' : '微信扫码支付' }}</h3>
          <button class="btn btn-outline btn-xs" @click="showPayment = false">&times;</button>
        </div>
        <div class="modal-body text-center">
          <div style="font-size:24px;font-weight:700;color:var(--primary);margin-bottom:16px">&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</div>

          <!-- Fixed QR Code mode -->
          <div v-if="fixedQrCode" style="margin-bottom:16px">
            <img :src="fixedQrCode" alt="QR Code" style="max-width:220px;border:1px solid var(--border-light);border-radius:8px" />
            <div style="font-size:14px;font-weight:600;margin-top:8px">请扫码转账 {{ (customAmount * pricePerUnit).toFixed(2) }} 元</div>
          </div>
          <div v-else-if="paymentLoading" class="empty-state" style="padding:20px 0;margin-bottom:16px">
            <div class="empty-state-text" style="font-size:13px">加载中...</div>
          </div>
          <div v-if="paymentError" class="alert alert-error" style="font-size:12px;margin-bottom:8px">{{ paymentError }}</div>
          <div v-if="paymentSuccess" class="alert alert-success" style="font-size:12px;margin-bottom:8px">{{ paymentSuccess }}</div>

          <!-- Manual confirm button -->
          <button v-if="fixedQrCode && !paymentSuccess" class="btn btn-primary btn-sm" style="width:100%;margin-bottom:8px" @click="submitManualPayment" :disabled="submittingPayment">
            {{ submittingPayment ? '提交中...' : '我已支付，通知管理员' }}
          </button>
          <p v-if="fixedQrCode" style="font-size:12px;color:var(--text-muted);margin-bottom:8px">付款后请点击上方按钮，管理员审核后到账</p>
        </div>
      </div>
    </div>

    <div class="text-center" style="padding:16px 0;color:var(--text-muted);font-size:12px">
      &copy;2026 EasyCode {{ t('copyright') }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const balance = ref('0.00'); const totalCost = ref('0.00'); const totalCalls = ref(0)
const customAmount = ref(1); const payMethod = ref('alipay'); const redeemCode = ref('')
const rechargeHistory = ref([]); const totalRecharged = ref('0.00')
const pricePerUnit = 1
const quickPlans = [{cny:10},{cny:50},{cny:100},{cny:200},{cny:500},{cny:1000},{cny:2000},{cny:5000}]

// Payment modal
const showPayment = ref(false)
const fixedQrCode = ref('')
const paymentLoading = ref(false)
const paymentError = ref('')
const paymentSuccess = ref('')
const submittingPayment = ref(false)
const toppingUp = ref(false); const redeeming = ref(false)

onMounted(async () => {
  try { const d = await api.getDashboard(); totalCalls.value = d.total_calls || 0; totalCost.value = (d.total_cost_yuan || 0).toFixed(2) } catch(e){}
  try { const u = await api.getMe(); balance.value = ((u.balance || 0) / 100).toFixed(2) } catch(e){}
  loadRechargeHistory()
  loadPaymentConfig()
})

async function loadPaymentConfig() {
  try { const cfg = await api.getPaymentConfig(); cachedPaymentConfig.value = cfg } catch(e) { /* */ }
}
const cachedPaymentConfig = ref({})

async function loadRechargeHistory() {
  try { const res = await api.getRechargeHistory(); rechargeHistory.value = res.items || []; totalRecharged.value = (rechargeHistory.value.filter(r=>r.status==='success').reduce((s,r)=>s+r.amount,0)/100).toFixed(2) } catch(e){}
}

async function startPayment() {
  if (!customAmount.value) return
  showPayment.value = true
  fixedQrCode.value = ''
  paymentError.value = ''
  paymentSuccess.value = ''
  paymentLoading.value = true

  // Check for fixed QR code in payment config
  const cfg = cachedPaymentConfig.value || {}
  const qrUrl = payMethod.value === 'alipay' ? cfg.alipay_qr_url : cfg.wechat_qr_url
  if (qrUrl) {
    fixedQrCode.value = qrUrl
    paymentLoading.value = false
    return
  }

  // Fallback: try dynamic Alipay API
  const amount = customAmount.value * pricePerUnit
  try {
    const res = await api.alipayRecharge(amount)
    fixedQrCode.value = res.qr_code
  } catch(e) {
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
    balance.value = ((cachedPaymentConfig.value?.balance || 0) / 100).toFixed(2)
    setTimeout(() => { showPayment.value = false; customAmount.value = 1; loadRechargeHistory() }, 2000)
  } catch(e) {
    paymentError.value = '提交失败: ' + e.message
  } finally { submittingPayment.value = false }
}

async function redeem() {
  if (!redeemCode.value) return
  redeeming.value = true
  try { await api.redeemCode(redeemCode.value); redeemCode.value = ''; loadRechargeHistory() }
  catch(e) { alert(e.message === 'code_not_found_or_used' ? '兑换码无效或已使用' : e.message) }
  finally { redeeming.value = false }
}

function fmtTime(iso) { return iso ? new Date(iso).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}) : '-' }
</script>

<style scoped>
.wallet-header { padding: 20px 24px; border-radius: var(--radius) var(--radius) 0 0; display: flex; justify-content: space-between; align-items: flex-start; }
.wallet-header-blue { background: linear-gradient(135deg, #6366f1, #4f46e5); }
.wallet-header-green { background: linear-gradient(135deg, #059669, #047857); }
.wallet-header-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.8); }
.wallet-stat-label { font-size: 10px; color: rgba(255,255,255,0.65); text-transform: uppercase; letter-spacing: 0.5px; }
.wallet-stat-value { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.3; }
.quick-amounts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.quick-amount-card { padding: 12px 8px; text-align: center; border: 1px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; transition: all 0.12s; background: #fff; }
.quick-amount-card:hover { border-color: var(--primary); background: var(--primary-light); }
.quick-amount-card.active { border-color: var(--primary); background: var(--primary-light); }
.modal-overlay { position: fixed; top:0;left:0;right:0;bottom:0; background: rgba(0,0,0,0.5); display:flex;align-items:center;justify-content:center; z-index:1000; }
.modal-content { background: var(--surface); border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); width:100%; }
.modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
.modal-body { padding: 20px; }
</style>
