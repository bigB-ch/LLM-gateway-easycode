<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">熔断器监控</h1>
      <button class="btn btn-outline" @click="refresh">刷新</button>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr><th>供应商</th><th>状态</th><th>失败次数</th><th>最后失败时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-if="breakers.length === 0">
              <td colspan="5"><div class="empty-state"><div class="empty-state-icon">&#x26A1;</div><div class="empty-state-text">暂无数据</div></div></td>
            </tr>
            <tr v-for="b in breakers" :key="b.provider">
              <td><strong>{{ b.provider }}</strong></td>
              <td><span :class="'badge ' + (b.status === 'closed' ? 'badge-success' : b.status === 'open' ? 'badge-danger' : 'badge-warning')">{{ b.status }}</span></td>
              <td>{{ b.failure_count }}</td>
              <td class="text-secondary">{{ b.last_failure_time > 0 ? new Date(b.last_failure_time * 1000).toLocaleString() : '-' }}</td>
              <td>
                <button v-if="b.status !== 'closed'" class="btn btn-danger btn-sm" @click="resetBreaker(b.provider)">重置</button>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gatewayApi } from '../gatewayApi'

const breakers = ref([])

async function loadBreakers() { try { breakers.value = await gatewayApi.listCircuitBreakers() } catch (e) { /* */ } }
onMounted(loadBreakers)

async function resetBreaker(provider) {
  try { await gatewayApi.resetCircuitBreaker(provider); await loadBreakers() } catch (e) { alert('重置失败: ' + e.message) }
}

async function refresh() { await loadBreakers() }
</script>
