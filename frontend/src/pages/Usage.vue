<template>
  <div>
    <h1 class="page-title mb-24">使用日志</h1>

    <div class="card">
      <div class="table-wrap" style="border:none" v-if="logs.length">
        <table class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>模型</th>
              <th>Token 用量</th>
              <th>费用</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id">
              <td class="text-secondary">{{ new Date(log.created_at).toLocaleString() }}</td>
              <td><span class="inline-code">{{ log.model }}</span></td>
              <td>{{ (log.prompt_tokens + log.completion_tokens).toLocaleString() }}</td>
              <td>&yen;{{ log.cost_yuan }}</td>
              <td><span :class="'badge ' + (log.status === 'success' ? 'badge-success' : 'badge-danger')">{{ log.status === 'success' ? '成功' : '失败' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">&#x1F4C4;</div>
        <div class="empty-state-text">暂无使用记录</div>
      </div>
    </div>

    <div v-if="logs.length" class="text-center mt-24" style="display:flex;justify-content:center;gap:8px">
      <button class="btn btn-outline" v-if="page > 1" @click="loadPage(page - 1)">上一页</button>
      <button class="btn btn-outline" @click="loadPage(page + 1)">下一页</button>
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
