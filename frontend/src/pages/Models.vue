<template>
  <div style="display:flex;gap:16px">
    <!-- ═══ Left filter panel ═══ -->
    <div class="card card-padded" style="width:220px;flex-shrink:0;align-self:flex-start;position:sticky;top:24px">
      <div class="flex-between mb-16">
        <h3 class="section-title">筛选</h3>
        <button class="btn btn-outline btn-xs" @click="resetFilters">重置</button>
      </div>

      <!-- Provider -->
      <div class="filter-group">
        <div class="filter-title">供应商</div>
        <label v-for="p in providerOptions" :key="p" class="filter-option">
          <input type="radio" v-model="fProvider" :value="p" />
          <span>{{ p === '' ? '全部供应商' : pMap[p] || p }}</span>
        </label>
      </div>

      <!-- Group -->
      <div class="filter-group">
        <div class="filter-title">可用令牌分组</div>
        <label v-for="g in groupOptions" :key="g" class="filter-option">
          <input type="radio" v-model="fGroup" :value="g" />
          <span>{{ g === '' ? '全部分组' : g }}</span>
        </label>
      </div>

      <!-- Billing type -->
      <div class="filter-group">
        <div class="filter-title">计费类型</div>
        <label v-for="b in billOptions" :key="b" class="filter-option">
          <input type="radio" v-model="fBilling" :value="b" />
          <span>{{ b === '' ? '全部类型' : b }}</span>
        </label>
      </div>

      <!-- Tags -->
      <div class="filter-group">
        <div class="filter-title">标签</div>
        <label v-for="t in tagOptions" :key="t" class="filter-option">
          <input type="radio" v-model="fTag" :value="t" />
          <span>{{ t === '' ? '全部标签' : t }}</span>
        </label>
      </div>

      <!-- Endpoint type -->
      <div class="filter-group" style="border-bottom:none">
        <div class="filter-title">端点类型</div>
        <label v-for="e in endpointOptions" :key="e" class="filter-option">
          <input type="radio" v-model="fEndpoint" :value="e" />
          <span>{{ e === '' ? '全部端点' : e }}</span>
        </label>
      </div>
    </div>

    <!-- ═══ Right content ═══ -->
    <div style="flex:1;min-width:0">
      <!-- Blue banner -->
      <div class="market-banner">
        <div>
          <div style="font-size:17px;font-weight:700">全部供应商（共 {{ filteredModels.length }} 个模型）</div>
          <div style="font-size:13px;opacity:0.75;margin-top:4px">聚合多家 AI 厂商模型资源，统一接口调用</div>
        </div>
      </div>

      <!-- Toolbar -->
      <div class="flex-between mb-16" style="margin-top:16px">
        <input v-model="searchQuery" class="form-input" placeholder="搜索模型名称..." style="width:260px;padding:7px 12px;font-size:13px" />
        <div style="display:flex;gap:6px">
          <button class="btn btn-outline btn-sm" @click="showPrice = !showPrice">{{ showPrice ? '隐藏' : '显示' }}价格</button>
          <button class="btn btn-outline btn-sm" @click="usdPrice = !usdPrice">{{ usdPrice ? '$' : '&yen;' }}</button>
          <button class="btn btn-outline btn-sm" @click="viewGrid = !viewGrid">{{ viewGrid ? '卡片' : '表格' }}视图</button>
        </div>
      </div>

      <!-- Model Cards Grid -->
      <div v-if="filteredModels.length" :class="viewGrid ? 'model-grid' : ''">
        <div v-for="m in filteredModels" :key="m.id" class="model-card card card-padded" :style="viewGrid ? {} : {display:'flex',alignItems:'center',gap:'16px',marginBottom:'8px'}">
          <div :style="viewGrid ? {} : {flex:1}">
            <div class="flex-between mb-8">
              <div>
                <span style="font-weight:700;font-size:15px">{{ m.id }}</span>
                <span class="badge badge-primary" style="margin-left:8px;font-size:10px">按量计费</span>
              </div>
              <input type="checkbox" v-if="!viewGrid" />
            </div>

            <div v-if="showPrice" style="display:flex;gap:16px;margin-top:8px" :style="viewGrid ? {} : {}">
              <div class="price-item">
                <div class="text-muted" style="font-size:10px">输入价格</div>
                <div style="font-weight:600;font-size:14px">{{ usdPrice ? '$' : '&yen;' }}{{ usdPrice ? m.input_price : m.input_price_cny }}/1M Tokens</div>
              </div>
              <div class="price-item">
                <div class="text-muted" style="font-size:10px">补全价格</div>
                <div style="font-weight:600;font-size:14px">{{ usdPrice ? '$' : '&yen;' }}{{ usdPrice ? m.output_price : m.output_price_cny }}/1M Tokens</div>
              </div>
              <div class="price-item">
                <div class="text-muted" style="font-size:10px">缓存读取</div>
                <div style="font-weight:600;font-size:14px;color:var(--success)">{{ usdPrice ? '$' : '&yen;' }}{{ usdPrice ? m.cache_price : m.cache_price_cny }}/1M Tokens</div>
              </div>
            </div>

            <div style="display:flex;gap:8px;margin-top:8px">
              <span class="text-muted" style="font-size:11px">{{ m.provider }}</span>
              <span class="text-muted" style="font-size:11px">{{ m.endpoint_type || 'openai' }}</span>
            </div>
          </div>

          <input type="checkbox" v-if="viewGrid" style="position:absolute;top:12px;right:12px" />
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="card card-padded">
        <div class="empty-state">
          <div class="empty-state-icon">&#x1F50D;</div>
          <div class="empty-state-text">暂无匹配模型</div>
          <div class="empty-state-sub">尝试调整筛选条件</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { gatewayApi } from '../gatewayApi'

const models = ref([])
const searchQuery = ref('')
const showPrice = ref(true)
const usdPrice = ref(true)
const viewGrid = ref(true)

// Filters
const fProvider = ref('')
const fGroup = ref('')
const fBilling = ref('')
const fTag = ref('')
const fEndpoint = ref('')

const providerOptions = ['', 'openai', 'anthropic', 'deepseek', 'google']
const groupOptions = ['', '默认']
const billOptions = ['', '按量计费', '按次计费']
const tagOptions = ['']
const endpointOptions = ['', 'openai', 'anthropic', 'gemini']

const pMap = { openai: 'OpenAI', anthropic: 'Anthropic', deepseek: 'DeepSeek', google: 'Google' }

const filteredModels = computed(() => {
  let list = models.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m => m.id.toLowerCase().includes(q))
  }
  if (fProvider.value) list = list.filter(m => m.provider === fProvider.value)
  if (fGroup.value) list = list.filter(m => (m.groups || []).includes(fGroup.value))
  if (fEndpoint.value) list = list.filter(m => (m.endpoint_type || 'openai') === fEndpoint.value)
  return list
})

// Real pricing: input/output/cache per 1M tokens (USD)
const REAL_PRICES = {
  // DeepSeek
  'deepseek-v4-flash':      { input: 0.14, output: 0.28, cache: 0.014 },
  'deepseek-v4-pro':         { input: 1.10, output: 4.40, cache: 0.11 },
  // OpenAI
  'gpt-4o':                 { input: 2.50, output: 10.00, cache: 1.25 },
  'gpt-4o-mini':            { input: 0.15, output: 0.60, cache: 0.075 },
  'gpt-4.1':                 { input: 2.00, output: 8.00, cache: 0.50 },
  'gpt-4':                   { input: 30.00, output: 60.00, cache: 15.00 },
  'gpt-3.5-turbo':           { input: 0.50, output: 1.50, cache: 0.25 },
  'o1':                      { input: 15.00, output: 60.00, cache: 7.50 },
  'o3':                      { input: 10.00, output: 40.00, cache: 5.00 },
  'o3-mini':                 { input: 1.10, output: 4.40, cache: 0.55 },
  // Anthropic
  'claude-sonnet-4-20250514': { input: 3.00, output: 15.00, cache: 0.30 },
  'claude-3-5-haiku-20241022': { input: 0.80, output: 4.00, cache: 0.08 },
  // Google
  'gemini-2.5-flash':         { input: 0.15, output: 0.60, cache: 0.0375 },
  'gemini-2.5-pro':           { input: 1.25, output: 5.00, cache: 0.3125 },
}

const USD_CNY_RATE = 7.28

function getPrice(id, field) {
  const p = REAL_PRICES[id]
  if (p) return p[field].toFixed(2)
  return '-'
}

function getPriceCNY(id, field) {
  const p = REAL_PRICES[id]
  if (p) return (p[field] * USD_CNY_RATE).toFixed(2)
  return '-'
}

onMounted(async () => {
  try {
    const data = await gatewayApi.listModels()
    models.value = (data.data || []).map(m => ({
      ...m,
      input_price: getPrice(m.id, 'input'),
      output_price: getPrice(m.id, 'output'),
      cache_price: getPrice(m.id, 'cache'),
      input_price_cny: getPriceCNY(m.id, 'input'),
      output_price_cny: getPriceCNY(m.id, 'output'),
      cache_price_cny: getPriceCNY(m.id, 'cache'),
      provider: m.provider || 'openai',
      endpoint_type: m.provider === 'google' ? 'gemini' : m.provider === 'anthropic' ? 'anthropic' : 'openai',
    }))
  } catch (e) { /* */ }
})

function resetFilters() {
  fProvider.value = ''; fGroup.value = ''; fBilling.value = ''
  fTag.value = ''; fEndpoint.value = ''
}
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
  text-align: center;
}
</style>
