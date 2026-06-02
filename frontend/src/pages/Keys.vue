<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>API Key 管理</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <div style="margin:24px 0">
      <button @click="showCreate = true" style="padding:10px 20px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">创建新 Key</button>
    </div>

    <div v-if="showCreate" style="background:#f9fafb;padding:24px;border-radius:8px;margin:16px 0">
      <h4>创建 API Key</h4>
      <input v-model="newKeyName" placeholder="Key 名称（可选）" style="padding:8px;margin:8px 0;width:100%" />
      <div style="margin:12px 0">
        <button @click="createKey" :disabled="creating" style="padding:8px 20px;background:#059669;color:white;border:none;border-radius:4px;cursor:pointer">
          {{ creating ? '创建中...' : '确认创建' }}
        </button>
        <button @click="showCreate = false" style="padding:8px 20px;margin-left:8px;background:#6b7280;color:white;border:none;border-radius:4px;cursor:pointer">取消</button>
      </div>
      <div v-if="newKey" style="background:#fef3c7;padding:16px;border-radius:4px;margin-top:16px">
        <strong>新 Key（仅显示一次，请立即复制保存）：</strong>
        <code style="display:block;margin-top:8px;word-break:break-all">{{ newKey }}</code>
      </div>
    </div>

    <div v-if="keys.length">
      <div v-for="key in keys" :key="key.id" style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:8px 0">
        <div style="display:flex;justify-content:space-between">
          <div>
            <code style="font-size:16px">{{ key.key_prefix }}****</code>
            <span v-if="key.name" style="margin-left:8px;color:#6b7280">{{ key.name }}</span>
            <span :style="'margin-left:8px;padding:2px 8px;border-radius:4px;font-size:12px;' + (key.status === 'active' ? 'background:#d1fae5;color:#059669' : 'background:#fee2e2;color:#dc2626')">{{ key.status }}</span>
          </div>
          <button v-if="key.status === 'active'" @click="revokeKey(key.id)" style="padding:4px 12px;background:#dc2626;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px">吊销</button>
        </div>
        <div style="color:#9ca3af;font-size:12px;margin-top:8px">
          创建于 {{ new Date(key.created_at).toLocaleDateString() }}
          <span v-if="key.last_used_at"> · 最后使用 {{ new Date(key.last_used_at).toLocaleString() }}</span>
        </div>
      </div>
    </div>
    <div v-else-if="!showCreate" style="color:#9ca3af;text-align:center;margin:48px 0">还没有 API Key</div>
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
  } catch (e) {
    alert(e.message)
  } finally {
    creating.value = false
  }
}

async function revokeKey(id) {
  if (!confirm('确定吊销此 Key？吊销后立即失效。')) return
  await api.revokeKey(id)
  const data = await api.listKeys()
  keys.value = data.items
}
</script>
