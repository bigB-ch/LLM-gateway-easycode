<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>用量明细</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <table style="width:100%;border-collapse:collapse;margin-top:24px">
      <thead>
        <tr style="border-bottom:2px solid #e5e7eb;text-align:left">
          <th style="padding:8px">时间</th>
          <th style="padding:8px">模型</th>
          <th style="padding:8px">Token</th>
          <th style="padding:8px">费用</th>
          <th style="padding:8px">状态</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" style="border-bottom:1px solid #f3f4f6">
          <td style="padding:8px;font-size:13px">{{ new Date(log.created_at).toLocaleString() }}</td>
          <td style="padding:8px;font-size:13px">{{ log.model }}</td>
          <td style="padding:8px;font-size:13px">{{ log.prompt_tokens + log.completion_tokens }}</td>
          <td style="padding:8px">¥{{ log.cost_yuan }}</td>
          <td style="padding:8px">
            <span :style="'padding:2px 6px;border-radius:4px;font-size:12px;' + (log.status === 'success' ? 'background:#d1fae5;color:#059669' : 'background:#fee2e2;color:#dc2626')">{{ log.status }}</span>
          </td>
        </tr>
        <tr v-if="logs.length === 0">
          <td colspan="5" style="text-align:center;padding:48px;color:#9ca3af">暂无使用记录</td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top:16px;text-align:center">
      <button v-if="page > 1" @click="loadPage(page - 1)" style="padding:8px 16px;margin:0 4px;border:1px solid #d1d5db;background:white;border-radius:4px;cursor:pointer">上一页</button>
      <button @click="loadPage(page + 1)" style="padding:8px 16px;margin:0 4px;border:1px solid #d1d5db;background:white;border-radius:4px;cursor:pointer">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const logs = ref([])
const page = ref(1)

async function loadPage(p) {
  page.value = p
  const data = await api.getUsage(p)
  logs.value = data.items
}

onMounted(() => loadPage(1))
</script>
