<template>
  <div style="display:flex;gap:16px">
    <!-- Left filter panel -->
    <n-card :bordered="true" size="small" style="width:220px;flex-shrink:0;align-self:flex-start;position:sticky;top:24px">
      <n-space align="center" justify="space-between" style="margin-bottom:16px">
        <n-text style="font-size:13px;font-weight:600">{{ t('filter') }}</n-text>
        <n-button size="tiny" @click="resetFilters">{{ t('reset') }}</n-button>
      </n-space>

      <div style="border-bottom:1px solid var(--border-light);padding-bottom:12px;margin-bottom:12px">
        <n-text style="font-size:12px;font-weight:600;display:block;margin-bottom:8px">供应商（{{ modelCount }}）</n-text>
        <n-radio-group v-model:value="fProvider" vertical :size="'small'">
          <n-radio v-for="p in providerOptions" :key="p.value" :value="p.value" style="font-size:12px">{{ p.label }}</n-radio>
        </n-radio-group>
      </div>

      <div style="border-bottom:1px solid var(--border-light);padding-bottom:12px;margin-bottom:12px">
        <n-text style="font-size:12px;font-weight:600;display:block;margin-bottom:8px">{{ t('billingType') }}</n-text>
        <n-radio-group v-model:value="fBilling" vertical :size="'small'">
          <n-radio value="" style="font-size:12px">{{ t('allTypes') }}</n-radio>
          <n-radio value="per_token" style="font-size:12px">{{ t('perToken') }}</n-radio>
          <n-radio value="per_use" style="font-size:12px">{{ t('perUse') }}</n-radio>
        </n-radio-group>
      </div>

      <div style="padding-bottom:0">
        <n-text style="font-size:12px;font-weight:600;display:block;margin-bottom:8px">{{ t('tags') }}</n-text>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          <span v-for="tg in tagOptions" :key="tg" :style="{cursor:'pointer',fontSize:'11px',padding:'3px 8px',borderRadius:'12px',border:'1px solid ' + (fTag === tg ? 'var(--primary)' : 'var(--border-light)'),background: fTag === tg ? 'var(--primary)' : 'transparent',color: fTag === tg ? '#fff' : 'var(--text-secondary)'}" @click="fTag = fTag === tg ? '' : tg">{{ tg || t('all') }}</span>
        </div>
      </div>
    </n-card>

    <!-- Right content -->
    <div style="flex:1;min-width:0">
      <!-- Blue banner -->
      <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;padding:24px 28px;border-radius:var(--radius-lg);margin-bottom:16px">
        <n-text style="font-size:17px;font-weight:700;display:block">{{ t('allSuppliers') }}（共 {{ filteredModels.length }} 个模型）</n-text>
        <n-text style="font-size:13px;opacity:0.75;display:block;margin-top:4px">{{ t('modelCountDesc') || '查看所有可用的AI模型供应商，包括众多知名供应商的模型。' }}</n-text>
      </div>

      <!-- Toolbar -->
      <n-space align="center" justify="space-between" style="margin-bottom:16px">
        <n-space :size="12" align="center" style="flex:1">
          <n-input v-model:value="searchQuery" :placeholder="t('searchModel')" size="small" style="width:260px" />
          <n-text depth="3" style="font-size:11px">&#x2139;&#xFE0F; {{ t('clickToCopyHint') }}</n-text>
        </n-space>
        <n-space :size="6">
          <n-button size="small" @click="showPrice = !showPrice">{{ showPrice ? t('hidePrice') : t('showPrice') }}</n-button>
          <n-button size="small" @click="showDesc = !showDesc">{{ showDesc ? '隐藏' : '显示' }}描述</n-button>
          <n-button size="small" @click="viewGrid = !viewGrid">{{ viewGrid ? t('cardView') : t('tableView') }}</n-button>
        </n-space>
      </n-space>

      <!-- Card view -->
      <div v-if="filteredModels.length && viewGrid" class="model-grid">
        <div v-for="m in filteredModels" :key="m.id" class="card" style="padding:16px;position:relative">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span v-if="m.icon" style="width:10px;height:10px;border-radius:50%;flex-shrink:0;background:modelColor(m.id)"></span>
            <span style="font-weight:700;font-size:14px;cursor:pointer;color:var(--primary);user-select:all" @click="copyModelId(m.id)" :title="t('clickToCopy')">{{ modelDisplayName(m.id) }}</span>
            <span style="font-size:10px;color:var(--text-muted);margin-left:auto;user-select:all">modelname: <span style="font-family:monospace;font-size:11px;color:var(--text-secondary)">{{ m.id }}</span></span>
          </div>
          <n-text depth="3" style="font-size:11px;display:block;margin-bottom:8px">{{ providerName(m.provider) }}</n-text>

          <div v-if="m.per_use > 0" style="margin-bottom:8px">
            <div style="padding:6px 12px;background:#fef3c7;border-radius:var(--radius-sm)">
              <n-text depth="3" style="font-size:10px">{{ t('modelPrice') }}</n-text>
              <n-text style="font-weight:600;font-size:14px;color:#d97706">&yen;{{ m.per_use_fmt }} / {{ t('perUseUnit') || '次' }}</n-text>
            </div>
          </div>

          <div v-if="showPrice && m.per_use === 0" style="display:flex;flex-direction:column;gap:4px;margin-bottom:8px">
            <div style="padding:6px 12px;background:#f8f9fb;border-radius:var(--radius-sm)">
              <n-text depth="3" style="font-size:10px">{{ t('inputPrice') }}</n-text>
              <n-text style="font-weight:600;font-size:13px">&yen;{{ m.input_fmt }} {{ t('per1MTokens') }}</n-text>
            </div>
            <div style="padding:6px 12px;background:#f8f9fb;border-radius:var(--radius-sm)">
              <n-text depth="3" style="font-size:10px">{{ t('outputPrice') }}</n-text>
              <n-text style="font-weight:600;font-size:13px">&yen;{{ m.output_fmt }} {{ t('per1MTokens') }}</n-text>
            </div>
            <div v-if="m.cache_price > 0" style="padding:6px 12px;background:#f8f9fb;border-radius:var(--radius-sm)">
              <n-text depth="3" style="font-size:10px">{{ t('cacheRead') }}</n-text>
              <n-text style="font-weight:600;font-size:13px;color:var(--success)">&yen;{{ m.cache_fmt }} {{ t('per1MTokens') }}</n-text>
            </div>
          </div>

          <div v-if="m.tags" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
            <span v-for="t in m.tags.split(',')" :key="t" class="badge" style="font-size:10px;background:rgba(99,102,241,0.1);color:var(--primary)">{{ t }}</span>
          </div>

          <n-text v-if="showDesc && m.description" depth="3" style="font-size:11px;display:block;margin-top:8px;line-height:1.4">{{ m.description }}</n-text>
        </div>
      </div>

      <!-- Table view -->
      <n-card v-else-if="filteredModels.length && !viewGrid" :bordered="true">
        <n-data-table :columns="tableColumns" :data="filteredModels" :bordered="false" :single-line="false" :min-height="100" />
      </n-card>

      <!-- Empty -->
      <n-card v-else :bordered="true">
        <n-empty :description="t('noModelsMatch') || '暂无匹配模型'" style="padding:40px 0">
          <template #extra>
            <n-text depth="3" style="font-size:12px">{{ t('adjustFilterHint') || '尝试调整筛选条件' }}</n-text>
          </template>
        </n-empty>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  NCard, NButton, NDataTable, NEmpty, NInput, NRadio, NRadioGroup,
  NSpace, NText,
} from 'naive-ui'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()
const message = useMessage()

const models = ref([])
const searchQuery = ref('')
const showPrice = ref(true)
const showDesc = ref(false)
const viewGrid = ref(true)
const fProvider = ref('')
const fBilling = ref('')
const fTag = ref('')

const providerOptions = ref([{ value: '', label: '全部供应商' }])
const tagOptions = ref([''])

const MODEL_DISPLAY = {
  'deepseek-v4-flash': 'DeepSeek V4 Flash',
  'deepseek-v4-pro': 'DeepSeek V4 Pro',
}
const PROVIDER_NAMES = { deepseek: 'DeepSeek' }
const MODEL_COLORS = { 'deepseek-v4-flash': '#4f46e5', 'deepseek-v4-pro': '#7c3aed' }

const tableColumns = [
  { title: t('model'), key: 'id', render: (row) => h('div', [
    h('div', { style: 'font-weight:600;cursor:pointer;color:var(--primary)' }, modelDisplayName(row.id)),
    h('div', { style: 'font-size:10px;color:var(--text-muted)' }, 'modelname: ' + row.id),
  ]) },
  { title: t('supplier'), key: 'provider', render: (row) => providerName(row.provider) },
  { title: t('inputPrice'), key: 'input_fmt', render: (row) => row.per_use === 0 ? '¥' + row.input_fmt + '/1M' : h('span', { style: 'color:#d97706' }, '¥' + row.per_use_fmt + '/次') },
  { title: t('outputPrice'), key: 'output_fmt', render: (row) => '¥' + row.output_fmt + '/1M' },
  { title: t('cacheRead'), key: 'cache_fmt', render: (row) => row.per_use > 0 ? '¥' + row.per_use_fmt + '/次' : '¥' + row.cache_fmt + '/1M' },
  { title: t('tags'), key: 'tags', render: (row) => (row.tags || '').split(',').slice(0, 3).map(t => h('span', { class: 'badge', style: 'font-size:10px;margin-right:2px' }, t)) },
]

const filteredModels = computed(() => {
  let list = models.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m => m.id.toLowerCase().includes(q) || PROVIDER_NAMES[m.provider]?.toLowerCase().includes(q))
  }
  if (fProvider.value) list = list.filter(m => m.provider === fProvider.value)
  if (fBilling.value === 'per_token') list = list.filter(m => !m.per_use)
  if (fBilling.value === 'per_use') list = list.filter(m => m.per_use)
  if (fTag.value) list = list.filter(m => (m.tags || '').includes(fTag.value))
  return list
})

const modelCount = computed(() => {
  const providers = new Set(models.value.map(m => m.provider))
  return providers.size
})

function copyModelId(id) {
  navigator.clipboard.writeText(id).catch(() => {
    const el = document.createElement('textarea')
    el.value = id; el.style.position = 'fixed'; el.style.left = '-9999px'
    document.body.appendChild(el); el.select(); document.execCommand('copy')
    document.body.removeChild(el)
  })
  message.success(t('copyModelSuccess'))
}

function modelDisplayName(id) {
  return MODEL_DISPLAY[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}
function providerName(key) { return PROVIDER_NAMES[key] || key }
function modelColor(id) { return MODEL_COLORS[id] || '#4f46e5' }
function resetFilters() { fProvider.value = ''; fBilling.value = ''; fTag.value = '' }

onMounted(async () => {
  try {
    const data = await gatewayApi.listModelCatalog()
    const allModels = (data.data || [])

    const providers = [...new Set(allModels.map(m => m.provider))]
    providerOptions.value = [
      { value: '', label: '全部供应商' },
      ...providers.map(p => ({ value: p, label: `${PROVIDER_NAMES[p] || p} (${allModels.filter(m => m.provider === p).length})` })),
    ]

    const allTags = new Set()
    allModels.forEach(m => (m.tags || '').split(',').forEach(t => { if (t.trim()) allTags.add(t.trim()) }))
    tagOptions.value = ['', ...allTags]

    models.value = allModels.map(m => ({
      ...m,
      id: m.model, input_fmt: m.input_price.toFixed(2), output_fmt: m.output_price.toFixed(2),
      cache_fmt: m.cache_price.toFixed(2), per_use_fmt: (m.per_use || 0).toFixed(2),
      tags: m.tags || '', description: m.description || '', icon: !!MODEL_COLORS[m.model],
      per_use: m.per_use || 0,
    }))
  } catch (e) { /* */ }
})
</script>

<style scoped>
.model-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; }
</style>
