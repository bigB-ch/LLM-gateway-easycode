<template>
  <div>
    <h1 class="page-title mb-24">钱包管理</h1>

    <div class="card card-padded mb-24">
      <div style="display:flex;align-items:center;gap:24px">
        <div class="stat-icon" style="width:56px;height:56px;border-radius:50%;background:var(--mc-blue-bg);color:var(--mc-blue);display:flex;align-items:center;justify-content:center;font-size:26px">&#x1F4B3;</div>
        <div>
          <div class="text-secondary">当前余额</div>
          <div style="font-size:32px;font-weight:700;color:var(--text);line-height:1.2">&yen;{{ balance }}</div>
        </div>
      </div>
    </div>

    <h3 class="section-title mb-16">购买套餐</h3>
    <div class="plan-grid">
      <div v-for="plan in plans" :key="plan.id" class="plan-card">
        <div class="plan-name">{{ plan.name }}</div>
        <div v-if="plan.description" class="text-secondary mt-8">{{ plan.description }}</div>
        <div class="plan-price">&yen;{{ plan.price_yuan }}</div>
        <div class="plan-detail">{{ (plan.token_quota / 10000).toFixed(0) }} 万 Token</div>
        <div class="plan-detail">{{ plan.duration_days }} 天有效</div>
        <button class="btn btn-primary" style="width:100%;margin-top:16px;padding:9px 0" @click="purchase(plan.id)">立即购买</button>
      </div>
    </div>
    <div v-if="plans.length === 0" class="card card-padded mt-16">
      <div class="empty-state">
        <div class="empty-state-icon">&#x1F4E6;</div>
        <div class="empty-state-text">暂无可购买套餐</div>
      </div>
    </div>
    <div v-if="message" class="alert alert-success mt-16">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const plans = ref([])
const message = ref('')
const balance = ref(0)

onMounted(async () => {
  const data = await api.getPlans()
  plans.value = data.items
  try {
    const user = await api.getMe()
    balance.value = (user.balance / 100).toFixed(2)
  } catch (e) { /* */ }
})

async function purchase(planId) {
  try {
    await api.purchasePlan(planId)
    message.value = '购买成功！'
    setTimeout(() => { message.value = '' }, 5000)
  } catch (e) {
    alert(e.message === 'insufficient_balance' ? '余额不足，请先充值' : '购买失败')
  }
}
</script>
