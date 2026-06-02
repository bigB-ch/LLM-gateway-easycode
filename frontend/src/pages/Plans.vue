<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>套餐购买</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin:24px 0">
      <div v-for="plan in plans" :key="plan.id" style="border:1px solid #e5e7eb;border-radius:8px;padding:24px;text-align:center">
        <h3>{{ plan.name }}</h3>
        <p v-if="plan.description" style="color:#6b7280">{{ plan.description }}</p>
        <div style="font-size:28px;font-weight:bold;margin:16px 0">¥{{ plan.price_yuan }}</div>
        <div style="color:#6b7280;margin:8px 0">{{ (plan.token_quota / 10000).toFixed(0) }} 万 Token</div>
        <div style="color:#6b7280;margin:8px 0">{{ plan.duration_days }} 天有效</div>
        <button @click="purchase(plan.id)" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer;margin-top:12px">购买</button>
      </div>
    </div>
    <div v-if="message" style="background:#d1fae5;padding:12px;border-radius:4px;margin:16px 0">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const plans = ref([])
const message = ref('')

onMounted(async () => {
  const data = await api.getPlans()
  plans.value = data.items
})

async function purchase(planId) {
  try {
    await api.purchasePlan(planId)
    message.value = '购买成功！'
  } catch (e) {
    alert(e.message === 'insufficient_balance' ? '余额不足，请先充值' : '购买失败')
  }
}
</script>
