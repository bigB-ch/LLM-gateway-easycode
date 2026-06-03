<template>
  <div>
    <!-- Left + Right cards -->
    <div style="display:flex;gap:16px;margin-bottom:16px">
      <!-- ═══ Left: 账户充值 ═══ -->
      <div class="card" style="flex:1">
        <!-- Blue header -->
        <div class="wallet-header wallet-header-blue">
          <div>
            <div class="wallet-header-title">账户充值</div>
            <div style="display:flex;gap:24px;margin-top:10px">
              <div>
                <div class="wallet-stat-label">当前余额</div>
                <div class="wallet-stat-value">&yen;{{ balance }}</div>
              </div>
              <div>
                <div class="wallet-stat-label">历史消耗</div>
                <div class="wallet-stat-value">&yen;{{ totalCost }}</div>
              </div>
              <div>
                <div class="wallet-stat-label">请求次数</div>
                <div class="wallet-stat-value">{{ totalCalls }}</div>
              </div>
            </div>
          </div>
          <router-link to="/usage" class="btn btn-outline btn-xs" style="background:rgba(255,255,255,0.2);color:#fff;border-color:rgba(255,255,255,0.3);align-self:flex-start">账单 &#x2197;</router-link>
        </div>

        <div class="card-padded">
          <!-- Custom amount -->
          <h3 class="section-title mb-12">自定义充值</h3>
          <div style="display:flex;gap:10px;align-items:flex-end;margin-bottom:20px">
            <div style="flex:1;max-width:200px">
              <label class="form-label">充值份数</label>
              <input v-model.number="customAmount" type="number" min="1" class="form-input" placeholder="输入份数" />
            </div>
            <div style="flex:1;max-width:120px">
              <label class="form-label">支付方式</label>
              <div class="form-input" style="display:flex;align-items:center;gap:6px;padding:9px 12px;background:#f5f5f5">
                <span style="font-size:16px">&#x1F4B3;</span> 支付宝
              </div>
            </div>
            <div>
              <label class="form-label">实付金额</label>
              <div style="font-weight:700;font-size:20px;color:var(--primary)">&yen;{{ (customAmount * pricePerUnit).toFixed(2) }}</div>
            </div>
            <button class="btn btn-primary" @click="topUp" :disabled="!customAmount">充值</button>
          </div>

          <!-- Quick amounts -->
          <h3 class="section-title mb-12">快捷档位</h3>
          <div class="quick-amounts">
            <div v-for="p in quickPlans" :key="p.usd"
              :class="'quick-amount-card ' + (customAmount === p.usd / pricePerUnit ? 'active' : '')"
              @click="customAmount = Math.round(p.usd / pricePerUnit)">
              <div style="font-weight:700;font-size:16px">&yen;{{ p.usd }}</div>
            </div>
          </div>

          <!-- Redeem code -->
          <div style="margin-top:20px;padding-top:20px;border-top:1px solid var(--border)">
            <h3 class="section-title mb-12">兑换码充值</h3>
            <div style="display:flex;gap:10px">
              <input v-model="redeemCode" class="form-input" placeholder="输入兑换码" style="flex:1;max-width:280px" />
              <button class="btn btn-outline" @click="redeem" :disabled="!redeemCode">兑换额度</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Right: 邀请奖励 ═══ -->
      <div class="card" style="flex:1">
        <!-- Green header -->
        <div class="wallet-header wallet-header-green">
          <div>
            <div class="wallet-header-title">邀请奖励</div>
            <div style="display:flex;gap:24px;margin-top:10px">
              <div>
                <div class="wallet-stat-label">待使用收益</div>
                <div class="wallet-stat-value">&yen;{{ pendingReward }}</div>
              </div>
              <div>
                <div class="wallet-stat-label">总收益</div>
                <div class="wallet-stat-value">&yen;{{ totalReward }}</div>
              </div>
              <div>
                <div class="wallet-stat-label">邀请人数</div>
                <div class="wallet-stat-value">{{ inviteCount }}</div>
              </div>
            </div>
          </div>
          <button class="btn btn-outline btn-xs" style="background:rgba(255,255,255,0.2);color:#fff;border-color:rgba(255,255,255,0.3);align-self:flex-start" @click="transferReward" :disabled="pendingReward <= 0">划转到余额</button>
        </div>

        <div class="card-padded">
          <!-- Referral link -->
          <h3 class="section-title mb-12">邀请链接</h3>
          <div style="display:flex;gap:8px;margin-bottom:24px">
            <code style="flex:1;background:#f8f9fb;padding:10px 14px;border-radius:6px;font-size:12px;word-break:break-all;font-family:var(--font-mono)">{{ referralUrl }}</code>
            <button class="btn btn-outline btn-sm" @click="copyText(referralUrl)">{{ linkCopied ? '已复制' : '复制' }}</button>
          </div>

          <!-- Reward rules -->
          <h3 class="section-title mb-12">奖励说明</h3>
          <div class="reward-rules">
            <div class="reward-rule">
              <span class="reward-dot">&#x25CF;</span>
              好友通过您的链接注册并充值后，您将获得充值金额的 <strong>10%</strong> 作为返利奖励
            </div>
            <div class="reward-rule">
              <span class="reward-dot">&#x25CF;</span>
              返利收益进入「待使用收益」，可随时划转到账户余额用于 API 调用
            </div>
            <div class="reward-rule">
              <span class="reward-dot">&#x25CF;</span>
              多邀多得，邀请人数和返利金额无上限，邀请越多收益越高
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Copyright footer -->
    <div class="text-center" style="padding:16px 0;color:var(--text-muted);font-size:12px">
      &copy;2026 EasyCode 版权所有
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const balance = ref('0.00')
const totalCost = ref('0.00')
const totalCalls = ref(0)
const customAmount = ref(1)
const redeemCode = ref('')
const linkCopied = ref(false)
const pendingReward = ref(0)
const totalReward = ref(0)
const inviteCount = ref(0)

const pricePerUnit = 1 // 1份 = ¥1
const quickPlans = [
  { usd: 50, cny: '50' },
  { usd: 100, cny: '100' },
  { usd: 200, cny: '200' },
  { usd: 300, cny: '300' },
  { usd: 500, cny: '500' },
  { usd: 800, cny: '800' },
  { usd: 1000, cny: '1000' },
  { usd: 2000, cny: '2000' },
]

const referralUrl = computed(() => {
  const aff = localStorage.getItem('aff_code') || 'Ylxt'
  return `${window.location.origin}/register?aff=${aff}`
})

onMounted(async () => {
  try {
    const d = await api.getDashboard()
    totalCalls.value = d.today_calls || 0
    totalCost.value = (d.today_cost_yuan || 0).toFixed(2)
  } catch (e) { /* */ }
  try {
    const user = await api.getMe()
    balance.value = ((user.balance || 0) / 100).toFixed(2)
  } catch (e) { /* */ }
})

function topUp() {
  const usd = (customAmount.value * pricePerUnit).toFixed(2)
  alert(`模拟充值：${customAmount.value} 份，合计 ¥${(customAmount.value * pricePerUnit).toFixed(2)}`)
}

function redeem() {
  alert(`兑换码「${redeemCode.value}」验证中...（功能开发中）`)
  redeemCode.value = ''
}

function transferReward() {
  alert('收益划转功能开发中')
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    linkCopied.value = true
    setTimeout(() => { linkCopied.value = false }, 2000)
  } catch (e) { /* */ }
}
</script>

<style scoped>
.wallet-header {
  padding: 20px 24px;
  border-radius: var(--radius) var(--radius) 0 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.wallet-header-blue { background: linear-gradient(135deg, #6366f1, #4f46e5); }
.wallet-header-green { background: linear-gradient(135deg, #059669, #047857); }

.wallet-header-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.8); }
.wallet-stat-label { font-size: 10px; color: rgba(255,255,255,0.65); text-transform: uppercase; letter-spacing: 0.5px; }
.wallet-stat-value { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.3; }

.quick-amounts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.quick-amount-card {
  padding: 12px 8px;
  text-align: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.12s;
  background: #fff;
}
.quick-amount-card:hover { border-color: var(--primary); background: var(--primary-light); }
.quick-amount-card.active { border-color: var(--primary); background: var(--primary-light); }

.reward-rules { display: flex; flex-direction: column; gap: 10px; }
.reward-rule { font-size: 13px; color: var(--text-secondary); line-height: 1.6; display: flex; align-items: flex-start; gap: 8px; }
.reward-dot { color: #059669; font-size: 8px; margin-top: 5px; flex-shrink: 0; }
</style>
