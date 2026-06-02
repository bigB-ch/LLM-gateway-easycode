<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <h2>LLM Gateway</h2>
      <nav>
        <router-link to="/admin" style="margin:0 8px">首页</router-link>
        <router-link to="/admin/keys" style="margin:0 8px">API Key</router-link>
        <router-link to="/admin/plans" style="margin:0 8px">套餐</router-link>
        <router-link to="/admin/usage" style="margin:0 8px">用量</router-link>
      </nav>
    </div>

    <div v-if="loading">加载中...</div>
    <template v-else>
      <div style="display:flex;gap:16px;margin:24px 0">
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">{{ dashboard.today_calls }}</div>
          <div style="color:#6b7280">今日调用</div>
        </div>
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">¥{{ dashboard.today_cost_yuan }}</div>
          <div style="color:#6b7280">今日消费</div>
        </div>
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">¥{{ dashboard.balance_yuan }}</div>
          <div style="color:#6b7280">账户余额</div>
        </div>
      </div>

      <div style="background:#f9fafb;padding:24px;border-radius:8px;margin:16px 0">
        <h4>快速开始</h4>
        <code style="background:#1f2937;color:#f3f4f6;padding:12px;display:block;border-radius:4px;font-size:13px">
          curl {{ apiBase }}/v1/chat/completions \<br/>
          &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY" \<br/>
          &nbsp;&nbsp;-d '{"model":"gpt-4","messages":[{"role":"user","content":"hello"}]}'
        </code>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const loading = ref(true)
const dashboard = ref({ today_calls: 0, today_cost_yuan: 0, balance_yuan: 0 })
const apiBase = window.location.origin

onMounted(async () => {
  try {
    dashboard.value = await api.getDashboard()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
