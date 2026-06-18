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
              <th style="text-align:center;background:#f0f9ff" colspan="3">成本价 (CNY/1M)</th>
              <th style="text-align:center;background:#fef3c7" colspan="3">用户实付价 (CNY/1M)</th>
              <th style="width:60px">操作</th>
            </tr>
            <tr>
              <th></th>
              <th>输入</th><th>输出</th><th>缓存/按次</th>
              <th>输入</th><th>输出</th><th>缓存/按次</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in modelList" :key="idx">
              <td><input v-model="m.name" class="form-input" style="padding:4px 8px;font-size:13px;width:100%" /></td>
              <td><input v-model.number="m.prompt" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><input v-model.number="m.completion" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" /></td>
              <td><input v-model.number="m.cache" type="number" step="0.01" min="0" class="form-input" style="padding:4px 8px;font-size:13px;width:100px" :placeholder="m.per_use > 0 ? '¥'+m.per_use+'/次' : '缓存'" /></td>
              <td class="price-display" style="background:#fef3c7">&yen;{{ fmt(m.prompt * markup) }}</td>
              <td class="price-display" style="background:#fef3c7">&yen;{{ fmt(m.completion * markup) }}</td>
              <td class="price-display" style="background:#fef3c7">{{ m.per_use > 0 ? '¥'+fmt(m.per_use * markup)+'/次' : m.cache > 0 ? '¥'+fmt(m.cache * markup) : '-' }}</td>
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

function fmt(v) { return Number(v || 0).toFixed(2) }
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
