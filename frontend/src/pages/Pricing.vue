<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">价格管理</n-h1>
      <n-space :size="8">
        <n-button size="small" @click="addModel">+ 添加模型</n-button>
        <n-button type="primary" size="small" :loading="saving" @click="savePricing">{{ saving ? '保存中...' : '保存全部' }}</n-button>
      </n-space>
    </n-space>

    <!-- Markup setting -->
    <n-card :bordered="true" size="small" style="margin-bottom:16px">
      <n-space align="flex-end" :size="16">
        <n-form-item label="全局加价倍率 (Markup)">
          <n-input-number v-model:value="markup" :min="1" :max="10" :step="0.1" style="width:120px" />
        </n-form-item>
        <n-text depth="3" style="font-size:12px;margin-bottom:8px">成本价 × 加价率 = 用户支付价</n-text>
      </n-space>
    </n-card>

    <!-- Pricing table -->
    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="modelList" :bordered="false" :single-line="false" />
    </n-card>

    <n-alert v-if="msg" :type="msg.includes('失') ? 'error' : 'success'" :bordered="true" closable @close="msg = ''" style="margin-top:12px;font-size:12px">
      {{ msg }}
    </n-alert>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import {
  NCard, NDataTable, NH1, NButton, NInput, NInputNumber,
  NSpace, NFormItem, NAlert, NText,
} from 'naive-ui'
import { api } from '../api'

const modelList = ref([])
const markup = ref(1.5)
const saving = ref(false)
const msg = ref('')

const tableColumns = [
  {
    title: '模型名称', key: 'name', width: 180,
    render: (row, idx) => h(NInput, {
      value: row.name, size: 'small',
      onUpdateValue: (v) => modelList.value[idx].name = v,
    }),
  },
  { title: '成本 — 输入', key: 'prompt', width: 110, render: (row, idx) => h(NInputNumber, {
    value: row.prompt, size: 'small', min: 0, step: 0.01, style: 'width:100px',
    onUpdateValue: (v) => modelList.value[idx].prompt = v || 0,
  }) },
  { title: '成本 — 输出', key: 'completion', width: 110, render: (row, idx) => h(NInputNumber, {
    value: row.completion, size: 'small', min: 0, step: 0.01, style: 'width:100px',
    onUpdateValue: (v) => modelList.value[idx].completion = v || 0,
  }) },
  {
    title: '成本 — 缓存/按次', key: 'cache', width: 140,
    render: (row, idx) => h(NInputNumber, {
      value: row.cache, size: 'small', min: 0, step: 0.01, placeholder: row.per_use > 0 ? '¥'+row.per_use+'/次' : '缓存', style: 'width:100px',
      onUpdateValue: (v) => modelList.value[idx].cache = v || 0,
    }),
  },
  {
    title: '实付 — 输入', key: 'user_prompt', width: 110,
    render: (row) => h('span', { style: 'color:var(--warning);font-weight:600' }, '¥' + fmt(row.prompt * markup.value)),
  },
  {
    title: '实付 — 输出', key: 'user_completion', width: 110,
    render: (row) => h('span', { style: 'color:var(--warning);font-weight:600' }, '¥' + fmt(row.completion * markup.value)),
  },
  {
    title: '实付 — 缓存/按次', key: 'user_cache', width: 140,
    render: (row) => h('span', { style: 'color:var(--warning)' },
      row.per_use > 0 ? '¥' + fmt(row.per_use * markup.value) + '/次'
      : row.cache > 0 ? '¥' + fmt(row.cache * markup.value) : '-'),
  },
  {
    title: '操作', key: 'actions', width: 60,
    render: (_, idx) => h(NButton, { size: 'tiny', color: '#dc2626', onClick: () => modelList.value.splice(idx, 1) }, { default: () => '删除' }),
  },
]

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
  } catch (e) { /* */ }
})

function fmt(v) { return Number(v || 0).toFixed(2) }
function addModel() { modelList.value.push({ name: '', prompt: 0, completion: 0, cache: 0, per_use: 0 }) }

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
  } catch (e) { msg.value = '保存失败: ' + e.message }
  finally { saving.value = false }
}
</script>
