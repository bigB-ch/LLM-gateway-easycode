<template>
  <div style="display:flex;gap:16px">
    <!-- Left filter panel -->
    <div class="card card-padded" style="width:220px;flex-shrink:0;align-self:flex-start;position:sticky;top:24px">
      <div class="flex-between mb-16">
        <h3 class="section-title">{{ t('filter') }}</h3>
        <button class="btn btn-outline btn-xs" @click="resetFilters">{{ t('reset') }}</button>
      </div>

      <!-- Provider -->
      <div class="filter-group">
        <div class="filter-title">供应商（{{ modelCount }}）</div>
        <label v-for="p in providerOptions" :key="p.value" class="filter-option">
          <input type="radio" v-model="fProvider" :value="p.value" />
          <span>{{ p.label }}</span>
        </label>
      </div>

      <!-- Billing type -->
      <div class="filter-group">
        <div class="filter-title">计费类型</div>
        <label v-for="b in billOptions" :key="b" class="filter-option">
          <input type="radio" v-model="fBilling" :value="b" />
          <span>{{ b === '' ? t('allTypes') : b }}</span>
        </label>
      </div>

      <!-- Tags -->
      <div class="filter-group" style="border-bottom:none">
        <div class="filter-title">标签</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          <span v-for="tg in tagOptions" :key="tg" class="tag-chip" :class="{ active: fTag === tg }" @click="fTag = fTag === tg ? '' : tg" style="cursor:pointer;font-size:11px;padding:3px 8px;border-radius:12px;border:1px solid var(--border-light)">{{ tg || t('all') }}</span>
        </div>
      </div>
    </div>

    <!-- Right content -->
    <div style="flex:1;min-width:0">
      <!-- Blue banner -->
      <div class="market-banner">
        <div>
          <div style="font-size:17px;font-weight:700">{{ t('allSuppliers') }}（共 {{ filteredModels.length }} 个模型）</div>
          <div style="font-size:13px;opacity:0.75;margin-top:4px">查看所有可用的AI模型供应商，包括众多知名供应商的模型。</div>
        </div>
      </div>

      <!-- Toolbar -->
      <div class="flex-between mb-16" style="margin-top:16px">
        <div style="display:flex;align-items:center;gap:12px;flex:1">
          <input v-model="searchQuery" class="form-input" placeholder="搜索模型名称..." style="width:260px;padding:7px 12px;font-size:13px" />
          <span class="text-muted" style="font-size:11px;display:flex;align-items:center;gap:4px">&#x2139;&#xFE0F; {{ t('clickToCopyHint') }}</span>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-outline btn-sm" @click="showPrice = !showPrice">{{ showPrice ? '隐藏' : '显示' }}价格</button>
          <button class="btn btn-outline btn-sm" @click="showDesc = !showDesc">{{ showDesc ? '隐藏' : '显示' }}描述</button>
          <button class="btn btn-outline btn-sm" @click="viewGrid = !viewGrid">{{ viewGrid ? '卡片' : '表格' }}视图</button>
        </div>
      </div>

      <!-- Model Cards / Table -->
      <div v-if="filteredModels.length">
        <!-- Card view -->
        <div v-if="viewGrid" class="model-grid">
          <div v-for="m in filteredModels" :key="m.id" class="model-card card card-padded">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
              <span v-if="m.icon" class="provider-dot" :style="{ background: modelColor(m.id) }"></span>
              <span style="font-weight:700;font-size:14px;cursor:pointer;color:var(--primary);user-select:all" @click="copyModelId(m.id)" :title="t('clickToCopy')">{{ modelDisplayName(m.id) }}</span>
              <span style="font-size:10px;color:var(--text-muted);margin-left:auto;user-select:all">modelname: <span style="font-family:monospace;font-size:11px;color:var(--text-secondary)">{{ m.id }}</span></span>
            </div>
            <div style="font-size:11px;color:var(--text-secondary);margin-bottom:8px">{{ providerName(m.provider) }}</div>

            <div v-if="m.per_use > 0" style="margin-bottom:8px">
              <div class="price-item" style="background:#fef3c7">
                <div class="text-muted" style="font-size:10px">模型价格</div>
                <div style="font-weight:600;font-size:14px;color:#d97706">&yen;{{ m.per_use_fmt }} / 次</div>
              </div>
            </div>

            <div v-if="showPrice && m.per_use === 0" style="display:flex;flex-direction:column;gap:4px;margin-bottom:8px">
              <div class="price-item">
                <div class="text-muted" style="font-size:10px">输入价格</div>
                <div style="font-weight:600;font-size:13px">&yen;{{ m.input_fmt }} / 1M Tokens</div>
              </div>
              <div class="price-item">
                <div class="text-muted" style="font-size:10px">补全价格</div>
                <div style="font-weight:600;font-size:13px">&yen;{{ m.output_fmt }} / 1M Tokens</div>
              </div>
              <div v-if="m.cache_price > 0" class="price-item">
                <div class="text-muted" style="font-size:10px">缓存读取价格</div>
                <div style="font-weight:600;font-size:13px;color:var(--success)">&yen;{{ m.cache_fmt }} / 1M Tokens</div>
              </div>
            </div>

            <div v-if="m.tags" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
              <span v-for="t in m.tags.split(',')" :key="t" class="badge" style="font-size:10px;background:rgba(99,102,241,0.1);color:var(--primary)">{{ t }}</span>
            </div>

            <div v-if="showDesc && m.description" class="text-muted" style="font-size:11px;margin-top:8px;line-height:1.4">{{ m.description }}</div>
          </div>
        </div>

        <!-- Table view -->
        <div v-else>
          <table class="data-table" style="width:100%">
            <thead>
              <tr>
                <th>{{ t('model') }}</th>
                <th>{{ t('supplier') }}</th>
                <th>{{ t('inputPrice') }}</th>
                <th>{{ t('outputPrice') }}</th>
                <th>{{ t('cacheOrPerUse') }}</th>
                <th>{{ t('tags') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in filteredModels" :key="m.id">
                <td>
                  <div style="font-weight:600;cursor:pointer;color:var(--primary)" @click="copyModelId(m.id)">{{ modelDisplayName(m.id) }}</div>
                  <div style="font-size:10px;color:var(--text-muted);user-select:all">modelname: <span style="font-family:monospace;color:var(--text-secondary)">{{ m.id }}</span></div>
                </td>
                <td>{{ providerName(m.provider) }}</td>
                <td v-if="m.per_use === 0">&yen;{{ m.input_fmt }}/1M</td>
                <td v-else style="color:#d97706">&yen;{{ m.per_use_fmt }}/次</td>
                <td>&yen;{{ m.output_fmt }}/1M</td>
                <td>{{ m.per_use > 0 ? '&yen;'+m.per_use_fmt+'/次' : '&yen;'+m.cache_fmt+'/1M' }}</td>
                <td><span v-for="t in (m.tags||'').split(',').slice(0,3)" :key="t" class="badge" style="font-size:10px;margin-right:2px">{{ t }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="card card-padded">
        <div class="empty-state">
          <div class="empty-state-icon">&#x1F50D;</div>
          <div class="empty-state-text">{{ t('noModelsMatch') }}</div>
          <div class="empty-state-sub">{{ t('adjustFilterHint') }}</div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toastMsg" style="position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 24px;border-radius:8px;font-size:13px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.2);transition:opacity 0.3s">
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()

const models = ref([])
const searchQuery = ref('')
const showPrice = ref(true)
const showDesc = ref(false)
const viewGrid = ref(true)

// Filters
const fProvider = ref('')
const fBilling = ref('')
const fTag = ref('')

const providerOptions = ref([{ value: '', label: '全部供应商' }])
const billOptions = ['', '按量计费', '按次计费']
const tagOptions = ref([''])

const MODEL_DISPLAY = {
  'deepseek-v4-flash': 'DeepSeek V4 Flash', 'deepseek-v4-pro': 'DeepSeek V4 Pro',
}
function copyModelId(id) {
  const el = document.createElement('textarea')
  el.value = id
  el.style.position = 'fixed'
  el.style.left = '-9999px'
  el.style.top = '-9999px'
  el.readOnly = true
  document.body.appendChild(el)
  el.select()
  el.setSelectionRange(0, el.value.length)
  document.execCommand('copy')
  document.body.removeChild(el)
  showToast(t('copyModelSuccess'))
}

const toastMsg = ref('')
let toastTimer = null
function showToast(msg) {
  toastMsg.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 2000)
}
function modelDisplayName(id) {
  return MODEL_DISPLAY[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}

const PROVIDER_NAMES = {
  deepseek: 'DeepSeek',
}

const MODEL_COLORS = {
  'deepseek-v4-flash': '#4f46e5',
  'deepseek-v4-pro': '#7c3aed',
}

function providerName(key) { return PROVIDER_NAMES[key] || key }
function modelColor(id) { return MODEL_COLORS[id] || '#4f46e5' }

const filteredModels = computed(() => {
  let list = models.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m => m.id.toLowerCase().includes(q) || PROVIDER_NAMES[m.provider]?.toLowerCase().includes(q))
  }
  if (fProvider.value) list = list.filter(m => m.provider === fProvider.value)
  if (fBilling.value === '按量计费') list = list.filter(m => m.per_use === 0)
  if (fBilling.value === '按次计费') list = list.filter(m => m.per_use > 0)
  if (fTag.value) list = list.filter(m => (m.tags || '').includes(fTag.value))
  return list
})

const modelCount = computed(() => {
  const providers = new Set(models.value.map(m => m.provider))
  return providers.size
})

function resetFilters() {
  fProvider.value = ''; fBilling.value = ''; fTag.value = ''
}

onMounted(async () => {
  try {
    const data = await gatewayApi.listModelCatalog()
    const allModels = (data.data || [])

    // Build provider filter
    const providers = [...new Set(allModels.map(m => m.provider))]
    providerOptions.value = [
      { value: '', label: '全部供应商' },
      ...providers.map(p => ({ value: p, label: `${PROVIDER_NAMES[p] || p} (${allModels.filter(m => m.provider === p).length})` }))
    ]

    // Build tag filter
    const allTags = new Set()
    allModels.forEach(m => {
      (m.tags || '').split(',').forEach(t => {
        if (t.trim()) allTags.add(t.trim())
      })
    })
    tagOptions.value = ['', ...allTags]

    models.value = allModels.map(m => ({
      ...m,
      id: m.model,
      input_fmt: (m.input_price).toFixed(2),
      output_fmt: (m.output_price).toFixed(2),
      cache_fmt: (m.cache_price).toFixed(2),
      per_use_fmt: (m.per_use).toFixed(2),
      tags: m.tags || '',
      description: m.description || '',
      icon: MODEL_COLORS[m.model] ? true : false,
      per_use: m.per_use || 0,
    }))
  } catch (e) {
    console.error('Failed to load model catalog:', e)
  }
})
</script>

<style scoped>
.filter-group {
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.filter-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}
.filter-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}
.filter-option:hover { color: var(--text); }
.filter-option input[type="radio"] { accent-color: var(--primary); }

.market-banner {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  padding: 24px 28px;
  border-radius: var(--radius-lg);
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.model-card { position: relative; transition: border-color 0.12s; }
.model-card:hover { border-color: #c0c5ce; }

.price-item {
  padding: 6px 12px;
  background: #f8f9fb;
  border-radius: var(--radius-sm);
}

.tag-chip.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.provider-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.data-table th {
  text-align: left;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-light);
}
.data-table td {
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}
</style>
