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
        <input v-model="searchQuery" class="form-input" placeholder="搜索模型名称..." style="width:260px;padding:7px 12px;font-size:13px" />
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
              <span v-if="m.icon" class="provider-dot" :style="{ background: iconColor(m.provider) }"></span>
              <span style="font-weight:700;font-size:14px">{{ modelDisplayName(m.id) }}</span>
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
                <td style="font-weight:600">{{ modelDisplayName(m.id) }}</td>
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
  'gpt-4o': 'GPT-4o', 'gpt-4o-mini': 'GPT-4o Mini', 'gpt-4.1': 'GPT-4.1',
  'gpt-4': 'GPT-4', 'gpt-4-turbo': 'GPT-4 Turbo', 'gpt-3.5-turbo': 'GPT-3.5 Turbo',
  'o1': 'o1', 'o3': 'o3', 'o3-mini': 'o3 Mini',
  'claude-3-opus': 'Claude 3 Opus', 'claude-3-sonnet': 'Claude 3 Sonnet',
  'claude-sonnet-4-20250514': 'Claude Sonnet 4', 'claude-3-5-haiku-20241022': 'Claude 3.5 Haiku',
  'gemini-pro': 'Gemini Pro', 'gemini-2.5-flash': 'Gemini 2.5 Flash', 'gemini-2.5-pro': 'Gemini 2.5 Pro',
  'deepseek-v3.2': 'DeepSeek V3.2', 'deepseek-v4-flash': 'DeepSeek V4 Flash', 'deepseek-v4-pro': 'DeepSeek V4 Pro',
  'qwen-turbo': 'Qwen Turbo', 'qwen-plus': 'Qwen Plus', 'qwen-max': 'Qwen Max', 'qwen3.6-plus': 'Qwen 3.6 Plus',
  'glm-4.7': 'GLM 4.7', 'glm-5': 'GLM 5', 'glm-5.1': 'GLM 5.1',
  'kimi-k2.5': 'Kimi K2.5', 'kimi-k2.6': 'Kimi K2.6',
  'MiniMax-M2.5': 'MiniMax M2.5',
  'doubao-seedance-2-0-260128': 'Doubao Seedance 2.0', 'doubao-seedance-2-0-fast-260128': 'Doubao Seedance 2.0 Fast',
  'kling-v1': 'Kling V1', 'kling-v1-5': 'Kling V1.5', 'kling-v1-6': 'Kling V1.6',
  'kling-v2-1': 'Kling V2.1', 'kling-v2-1-master': 'Kling V2.1 Master', 'kling-v2-master': 'Kling V2 Master',
  'kling-v2-5-turbo': 'Kling V2.5 Turbo', 'kling-v2-6': 'Kling V2.6',
  'kling-v3': 'Kling V3', 'kling-v3-omni': 'Kling V3 Omni', 'kling-video-o1': 'Kling Video O1',
}
function modelDisplayName(id) {
  return MODEL_DISPLAY[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}

const PROVIDER_NAMES = {
  openai: 'OpenAI',
  anthropic: 'Anthropic Claude',
  google: 'Google Gemini',
  deepseek: 'DeepSeek',
  qwen: '阿里巴巴 / 通义千问',
  zhipu: '智谱 AI',
  moonshot: 'Moonshot / Kimi',
  doubao: '字节跳动 / 豆包',
  minimax: 'MiniMax',
  kling: '快手可灵 Kling',
}

const PROVIDER_COLORS = {
  openai: '#10a37f', anthropic: '#d97757', google: '#1c69ff',
  deepseek: '#4f46e5', qwen: '#615ced', zhipu: '#1677ff',
  moonshot: '#8b5cf6', doubao: '#f59e0b', minimax: '#ef4444',
  kling: '#ec4899',
}

function providerName(key) { return PROVIDER_NAMES[key] || key }
function iconColor(key) { return PROVIDER_COLORS[key] || '#999' }

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
      icon: PROVIDER_COLORS[m.provider] ? true : false,
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
