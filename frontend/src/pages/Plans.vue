<template>
  <div class="plans-page">
    <!-- ── Balance Bar ── -->
    <div class="balance-bar">
      <div class="balance-glow" />
      <div class="balance-inner">
        <div>
          <div class="balance-label">{{ t('currentBalance') }}</div>
          <div class="balance-num">
            <span class="balance-sym">&yen;</span>{{ balance }}
          </div>
        </div>
        <div class="balance-meta">
          <div class="balance-stat">
            <span class="balance-stat-lbl">{{ t('totalSpent') }}</span>
            <span class="balance-stat-val">&yen;{{ totalCost }}</span>
          </div>
          <div class="balance-stat">
            <span class="balance-stat-lbl">{{ t('requestCount') }}</span>
            <span class="balance-stat-val">{{ totalCalls }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="plans-body">
      <!-- Left -->
      <div class="plans-main">
        <!-- Quick Recharge -->
        <div class="plans-section">
          <div class="plans-section-hd">
            <h3>快捷充值</h3>
          </div>
          <div class="quick-grid">
            <button
              v-for="p in quickTiers"
              :key="p"
              :class="['quick-chip', { 'quick-chip--on': customAmount === Math.round(p / pricePerUnit) }]"
              @click="customAmount = Math.round(p / pricePerUnit)"
            >&yen;{{ p }}</button>
          </div>
        </div>

        <!-- Custom Recharge -->
        <div class="plans-section">
          <div class="plans-section-hd">
            <h3>自定义充值</h3>
          </div>
          <div class="cust-form">
            <div class="cust-row">
              <div class="cust-input-box">
                <span class="cust-input-pre">&yen;</span>
                <input v-model.number="customAmount" type="number" min="1" class="cust-input" placeholder="金额" />
              </div>
              <div class="cust-methods">
                <span class="cust-method cust-method--on">
                  <svg width="15" height="15" viewBox="0 0 20 20" fill="none"><rect x="1" y="3" width="18" height="14" rx="2.5" stroke="currentColor" stroke-width="1.4"/><path d="M6 10l3 3 5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  支付宝
                </span>
              </div>
              <div class="cust-total">
                应付 <strong>&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</strong>
              </div>
              <button class="cust-btn" :disabled="!customAmount" @click="startPayment">
                充值
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Redeem Code -->
        <div class="plans-section plans-section--dim">
          <div class="plans-section-hd">
            <h3>兑换码充值</h3>
            <span class="dim-badge">功能改进中</span>
          </div>
          <div class="redeem-row">
            <input v-model="redeemCode" placeholder="输入兑换码" disabled class="redeem-input" />
            <button disabled class="redeem-btn">兑换</button>
          </div>
        </div>
      </div>

      <!-- Right: History -->
      <div class="plans-side">
        <div class="plans-section plans-section--side">
          <div class="plans-section-hd">
            <h3>充值记录</h3>
            <span class="hist-total">&yen;{{ totalRecharged }}</span>
          </div>
          <div v-if="history.length" class="hist-scroll">
            <div v-for="(r, i) in history" :key="r.id" class="hist-row">
              <span :class="['hist-dot', r.status]" />
              <div class="hist-body">
                <div class="hist-top">
                  <span>{{ r.method === 'alipay' ? '支付宝' : r.method === 'wechat' ? '微信' : '兑换码' }}</span>
                  <span :class="['hist-val', r.status]">+&yen;{{ (r.amount / 100).toFixed(2) }}</span>
                </div>
                <div class="hist-bot">
                  <span class="hist-time">{{ fmtTime(r.created_at) }}</span>
                  <span :class="['hist-tag', r.status]">{{ r.status === 'success' ? '已到账' : '待审核' }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="hist-empty">
            <svg width="30" height="30" viewBox="0 0 30 30" fill="none"><rect x="4" y="7" width="22" height="17" rx="3" stroke="currentColor" stroke-width="1.3" stroke-dasharray="3 3"/><path d="M11 15l3 3 5-5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <p>暂无充值记录</p>
          </div>
        </div>
      </div>
    </div>

    <!-- end -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const balance = ref('0.00')
const totalCost = ref('0.00')
const totalCalls = ref(0)
const customAmount = ref(1)
const redeemCode = ref('')
const history = ref([])
const totalRecharged = ref('0.00')
const pricePerUnit = 1
const quickTiers = [10, 50, 100, 200, 500, 1000, 2000, 5000]

onMounted(async () => {
  try { const d = await api.getDashboard(); totalCalls.value = d.total_calls || 0; totalCost.value = (d.total_cost_yuan || 0).toFixed(2) } catch (_) {}
  try { const u = await api.getMe(); balance.value = ((u.balance || 0) / 100).toFixed(2) } catch (_) {}
  loadHistory(); checkReturn()
})

function checkReturn() {
  const s = new URLSearchParams(window.location.search).get('payment')
  if (!s) return; window.history.replaceState({}, '', '/plans')
  if (s === 'success') { refreshBalance(); loadHistory() }
}
async function refreshBalance() { try { const u = await api.getMe(); balance.value = ((u.balance || 0) / 100).toFixed(2) } catch (_) {} }
async function loadHistory() {
  try {
    const r = await api.getRechargeHistory()
    history.value = (r.items || []).filter(x => x.status === 'success')
    totalRecharged.value = (history.value.reduce((s, x) => s + x.amount, 0) / 100).toFixed(2)
  } catch (_) {}
}

async function startPayment() {
  if (!customAmount.value) return
  try {
    const r = await api.alipayPagePayment(customAmount.value * pricePerUnit, window.location.origin + '/plans')
    window.location.href = r.redirect_url
  } catch (e) {
    alert('创建支付失败: ' + (e.message || '请检查支付宝配置'))
  }
}

function fmtTime(iso) { return iso ? new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-' }
</script>

<style scoped>
/* ── Page ── */
.plans-page { max-width: 960px; }

/* ── Balance Bar ── */
.balance-bar {
  position: relative; overflow: hidden; border-radius: 12px;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  padding: 20px 24px; margin-bottom: 20px;
}
.balance-glow {
  position: absolute; top: -50%; right: -8%; width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(251,191,36,0.1) 0%, transparent 70%);
  pointer-events: none;
}
.balance-inner { position: relative; z-index: 1; display: flex; align-items: flex-end; justify-content: space-between; }
.balance-label { font-size: 12px; color: rgba(255,255,255,0.45); margin-bottom: 2px; }
.balance-num { font-size: 36px; font-weight: 700; color: #fff; letter-spacing: -1px; line-height: 1; }
.balance-sym { font-size: 18px; font-weight: 600; color: rgba(255,255,255,0.5); margin-right: 2px; }
.balance-meta { display: flex; gap: 24px; padding-bottom: 4px; }
.balance-stat { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.balance-stat-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.35); }
.balance-stat-val { font-size: 15px; font-weight: 600; color: rgba(255,255,255,0.8); }

/* ── Body ── */
.plans-body { display: grid; grid-template-columns: 1fr 280px; gap: 20px; align-items: start; }
.plans-main { display: flex; flex-direction: column; gap: 16px; }

/* ── Section ── */
.plans-section {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px 20px;
}
.plans-section--side { padding: 18px 16px; display: flex; flex-direction: column; max-height: 500px; position: sticky; top: 16px; }
.plans-section-hd { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.plans-section-hd h3 { margin: 0; font-size: 14px; font-weight: 600; color: #111; }
.plans-section-sub { font-size: 12px; color: #9ca3af; }

/* ── Quick Grid ── */
.quick-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; }
.quick-chip {
  padding: 10px 2px; text-align: center;
  border: 1.5px solid #e5e7eb; border-radius: 8px; background: #fff;
  cursor: pointer; font-family: inherit;
  font-size: 15px; font-weight: 700; color: #1f2937;
  transition: all 0.12s;
}
.quick-chip:hover { border-color: #f59e0b; background: #fffbeb; }
.quick-chip--on { border-color: #f59e0b; background: #fffbeb; box-shadow: 0 0 0 3px rgba(245,158,11,0.1); }

/* ── Redeem ── */
.plans-section--dim { opacity: 0.4; pointer-events: none; }
.dim-badge { font-size: 10px; padding: 2px 7px; border-radius: 999px; background: #fef3c7; color: #d97706; font-weight: 500; }
.redeem-row { display: flex; gap: 8px; }
.redeem-input { flex: 1; padding: 9px 12px; border: 1.5px solid #e5e7eb; border-radius: 8px; font-size: 13px; font-family: inherit; outline: none; background: #f9fafb; }
.redeem-btn { padding: 9px 18px; border: none; border-radius: 8px; background: #e5e7eb; color: #9ca3af; font-size: 13px; font-weight: 500; font-family: inherit; }

/* ── Custom ── */
.cust-form { }
.cust-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.cust-input-box {
  display: flex; align-items: center;
  border: 1.5px solid #d1d5db; border-radius: 8px; padding: 0 12px;
  transition: border-color 0.15s;
}
.cust-input-box:focus-within { border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.08); }
.cust-input-pre { font-size: 16px; font-weight: 600; color: #9ca3af; margin-right: 2px; }
.cust-input { border: none; outline: none; font-size: 18px; font-weight: 600; color: #111; width: 100px; padding: 9px 0; background: transparent; font-family: inherit; -moz-appearance: textfield; }
.cust-input::-webkit-inner-spin-button { display: none; }
.cust-methods { display: flex; }
.cust-method {
  display: flex; align-items: center; gap: 4px;
  padding: 8px 13px; border: 1.5px solid #2563eb; border-radius: 8px;
  background: #eff6ff; color: #2563eb;
  font-size: 12px; font-weight: 500;
}
.cust-total { font-size: 13px; color: #6b7280; white-space: nowrap; }
.cust-total strong { font-size: 17px; font-weight: 700; color: #111; margin-left: 3px; }
.cust-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 9px 22px; border: none; border-radius: 8px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; font-family: inherit; transition: all 0.12s;
}
.cust-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(245,158,11,0.3); }
.cust-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── History ── */
.hist-total { font-size: 13px; font-weight: 700; color: #059669; }
.hist-scroll { flex: 1; overflow-y: auto; margin: 0 -16px; padding: 0 16px; }
.hist-row { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
.hist-row:last-child { border-bottom: none; }
.hist-dot { width: 7px; height: 7px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
.hist-dot.success { background: #10b981; }
.hist-dot.pending { background: #f59e0b; }
.hist-body { flex: 1; min-width: 0; }
.hist-top { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #374151; }
.hist-val { font-size: 13px; font-weight: 700; }
.hist-val.success { color: #059669; }
.hist-val.pending { color: #6b7280; }
.hist-bot { display: flex; justify-content: space-between; align-items: center; margin-top: 3px; }
.hist-time { font-size: 11px; color: #9ca3af; }
.hist-tag { font-size: 10px; padding: 1px 6px; border-radius: 999px; font-weight: 500; }
.hist-tag.success { color: #059669; background: #ecfdf5; }
.hist-tag.pending { color: #d97706; background: #fef3c7; }
.hist-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 36px 0; color: #9ca3af; font-size: 13px; }

@media (max-width: 820px) {
  .plans-body { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: repeat(4, 1fr); }
  .balance-inner { flex-direction: column; align-items: flex-start; gap: 14px; }
}
</style>
