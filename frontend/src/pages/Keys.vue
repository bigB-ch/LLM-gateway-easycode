<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">令牌管理</h1>
      <button class="btn btn-primary" @click="showCreate = true" v-if="!showCreate">+ 创建令牌</button>
    </div>

    <div v-if="showCreate" class="card card-padded mb-24">
      <div class="form-group">
        <label class="form-label">令牌名称</label>
        <input v-model="newKeyName" class="form-input" placeholder="例如：生产环境" style="max-width:360px" />
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" @click="createKey" :disabled="creating">{{ creating ? '创建中...' : '确认创建' }}</button>
        <button class="btn btn-outline" @click="showCreate = false">取消</button>
      </div>
      <div v-if="newKey" class="alert alert-success mt-16">
        <strong>新令牌已生成（仅显示一次，请立即复制保存）：</strong>
        <div class="code-block mt-8">{{ newKey }}</div>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none" v-if="keys.length">
        <table class="data-table">
          <thead>
            <tr>
              <th>令牌</th>
              <th>名称</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>最后使用</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in keys" :key="key.id">
              <td><span class="key-masked">{{ key.key_prefix }}****</span></td>
              <td><span class="text-secondary">{{ key.name || '-' }}</span></td>
              <td><span :class="'badge ' + (key.status === 'active' ? 'badge-success' : 'badge-danger')">{{ key.status === 'active' ? '活跃' : '已吊销' }}</span></td>
              <td class="text-secondary">{{ new Date(key.created_at).toLocaleDateString() }}</td>
              <td class="text-secondary">{{ key.last_used_at ? new Date(key.last_used_at).toLocaleString() : '-' }}</td>
              <td>
                <button v-if="key.status === 'active'" class="btn btn-danger btn-sm" @click="revokeKey(key.id)">吊销</button>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!showCreate" class="empty-state">
        <div class="empty-state-icon">&#x1F511;</div>
        <div class="empty-state-text">暂无令牌</div>
        <div class="empty-state-sub">点击上方按钮创建您的第一个 API 令牌</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const keys = ref([])
const showCreate = ref(false)
const newKeyName = ref('')
const newKey = ref('')
const creating = ref(false)

onMounted(async () => {
  const data = await api.listKeys()
  keys.value = data.items
})

async function createKey() {
  creating.value = true
  try {
    const data = await api.createKey(newKeyName.value || null)
    newKey.value = data.api_key
    const list = await api.listKeys()
    keys.value = list.items
    newKeyName.value = ''
  } catch (e) { alert(e.message) } finally { creating.value = false }
}

async function revokeKey(id) {
  if (!confirm('确定吊销此令牌？吊销后立即失效。')) return
  await api.revokeKey(id)
  const data = await api.listKeys()
  keys.value = data.items
}
</script>
