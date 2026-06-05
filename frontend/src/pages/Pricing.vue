<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">价格管理</h1>
      <div style="display:flex;gap:8px">
        <button class="btn btn-outline btn-sm" @click="addModel">+ 添加模型</button>
        <button class="btn btn-primary btn-sm" @click="savePricing" :disabled="saving">{{ saving ? '保存中...' : '保存全部' }}</button>
      </div>
    </div>

    <!-- Markup setting -->
    <div class="card card-padded mb-16">
      <div style="display:flex;gap:16px;align-items:flex-end">
        <div>
          <label class="form-label">全局加价倍率 (Markup)</label>
          <input v-model.number="markup" type="number" step="0.1" min="1" max="10" class="form-input" style="width:120px" />
        </div>
        <span class="text-muted" style="font-size:12px;margin-bottom:8px">成本价 × 加价率 = 用户支付价</span>
      </div>
    </div>

    <!-- Pricing table -->
    <div class="card">
      <div class="table-wrap" style="border:none;overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th style="min-width:180px">模型名称</th>
              <th>输入价格 (CNY/1M)</th>
              <th>输出价格 (CNY/1M)</th>
              <th>缓存价格 (CNY/1M)</th>
              <th>按次价格 (CNY)</th>
              <th style="width:60px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in modelList" :key="idx">
              <td><input v-model="m.name" class="form-input" style="padding:4px 8px;font-size:13px;width:100%" /></td>
              <td><input v-model.number="m.prompt" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><input v-model.number="m.completion" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><input v-model.number="m.cache" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><input v-model.number="m.per_use" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><button class="btn btn-danger btn-xs" @click="modelList.splice(idx,1)">删除</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="msg" :class="msg.includes('失') ? 'alert alert-error' : 'alert alert-success'" style="margin-top:12px;font-size:12px">{{ msg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const modelList = ref([])
const markup = ref(1.5)
const saving = ref(false)
const msg = ref('')

onMounted(async () => {
  try {
    const res = await api.getPricing()
    const data = res.data || {}
    markup.value = data.markup || 1.5
    const models = data.models || {}
    modelList.value = Object.entries(models).map(([name, p]) => ({
      name, prompt: p.prompt || 0, completion: p.completion || 0,
      cache: p.cache || 0, per_use: p.per_use || 0,
    }))
  } catch(e) { /* */ }
})

function addModel() {
  modelList.value.push({ name: '', prompt: 0, completion: 0, cache: 0, per_use: 0 })
}

async function savePricing() {
  saving.value = true; msg.value = ''
  const models = {}
  for (const m of modelList.value) {
    if (!m.name) continue
    models[m.name] = { prompt: m.prompt || 0, completion: m.completion || 0 }
    if (m.cache) models[m.name].cache = m.cache
    if (m.per_use) models[m.name].per_use = m.per_use
  }
  try {
    await api.savePricing({ models, markup: markup.value })
    msg.value = '保存成功'
  } catch(e) { msg.value = '保存失败: ' + e.message } finally { saving.value = false }
}
</script>
