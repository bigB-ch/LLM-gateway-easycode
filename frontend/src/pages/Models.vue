<template>
  <div>
    <!-- Provider filter tabs + search -->
    <div class="model-filter-bar">
      <button
        v-for="p in providerTabs"
        :key="p.value"
        :class="['model-tab', fProvider === p.value && 'active']"
        @click="fProvider = p.value"
      >{{ p.label }}</button>
      <div style="flex:1" />
      <input v-model="searchQuery" class="model-search" placeholder="搜索模型..." />
    </div>

    <!-- Featured section -->
    <template v-if="featuredModels.length">
      <div class="section-heading">精选推荐</div>
      <div class="featured-grid">
        <div
          v-for="m in featuredModels"
          :key="m.id"
          class="featured-card"
          style="cursor:pointer"
          @click="$router.push('/models/' + m.id)"
        >
          <div :class="['featured-banner', 'banner-' + colorKey(m.provider)]">
            <div class="featured-icon">{{ providerInitial(m.provider) }}</div>
            <div>
              <div class="featured-name">{{ displayName(m.id) }}</div>
              <div class="featured-sub">{{ m.provider }}</div>
            </div>
          </div>
          <div class="featured-body">
            <div class="tag-row">
              <span v-for="tg in splitTags(m.tags)" :key="tg" class="mtag">{{ tg }}</span>
            </div>
            <p class="mdesc">{{ m.description || '高性能大语言模型' }}</p>
            <div class="price-row">
              <span v-if="m.per_use > 0" class="pchip pchip--amber">¥{{ m.per_use_fmt }}/次</span>
              <template v-else>
                <span class="pchip">输入 ¥{{ m.input_fmt }}/1M</span>
                <span class="pchip">输出 ¥{{ m.output_fmt }}/1M</span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- All models grid -->
    <div class="section-heading" style="margin-top:24px">
      全部模型（{{ filteredModels.length }}）
    </div>
    <div v-if="filteredModels.length" class="model-grid">
      <div
        v-for="m in filteredModels"
        :key="m.id"
        class="model-card"
        @click="$router.push('/models/' + m.id)"
      >
        <div class="mc-header">
          <div :class="['mc-icon', 'icon-' + colorKey(m.provider)]">
            {{ providerInitial(m.provider) }}
          </div>
          <div style="min-width:0">
            <div class="mc-name">{{ displayName(m.id) }}</div>
            <div class="mc-provider">{{ m.provider }}</div>
          </div>
        </div>
        <p class="mc-desc">{{ m.description || '高性能大语言模型' }}</p>
        <div class="price-row" style="margin-top:auto">
          <span v-if="m.per_use > 0" class="pchip pchip--amber">¥{{ m.per_use_fmt }}/次</span>
          <template v-else>
            <span class="pchip">¥{{ m.input_fmt }}/1M in</span>
            <span class="pchip">¥{{ m.output_fmt }}/1M out</span>
          </template>
        </div>
      </div>
    </div>
    <div v-else class="model-empty">暂无匹配模型，尝试调整筛选条件</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { gatewayApi } from '../gatewayApi'

const FEATURED_IDS = ['claude-sonnet-4-5', 'deepseek-r1']

const DISPLAY_NAMES = {
  'deepseek-v4-flash': 'DeepSeek V4 Flash',
  'deepseek-v4-pro': 'DeepSeek V4 Pro',
  'deepseek-r1': 'DeepSeek R1',
  'claude-sonnet-4-5': 'Claude Sonnet 4.5',
  'claude-opus-4-5': 'Claude Opus 4.5',
  'gpt-4o': 'GPT-4o',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gemini-1.5-pro': 'Gemini 1.5 Pro',
}

const PROVIDER_LABELS = {
  anthropic: 'Anthropic', openai: 'OpenAI', deepseek: 'DeepSeek',
  google: 'Google', mistral: 'Mistral',
}

const COLOR_KEYS = {
  anthropic: 'purple', openai: 'mint', deepseek: 'blue',
  google: 'yellow', mistral: 'orange',
}

const models = ref([])
const searchQuery = ref('')
const fProvider = ref('')

const providerTabs = computed(() => {
  const providers = [...new Set(models.value.map(m => m.provider))]
  return [
    { value: '', label: '全部' },
    ...providers.map(p => ({ value: p, label: PROVIDER_LABELS[p] || p })),
  ]
})

const filteredModels = computed(() => {
  let list = models.value
  if (fProvider.value) list = list.filter(m => m.provider === fProvider.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m =>
      m.id.toLowerCase().includes(q) || (m.description || '').toLowerCase().includes(q)
    )
  }
  return list
})

const featuredModels = computed(() =>
  FEATURED_IDS.map(id => models.value.find(m => m.id === id)).filter(Boolean)
)

function displayName(id) {
  return DISPLAY_NAMES[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}
function colorKey(provider) { return COLOR_KEYS[provider] || 'pink' }
function providerInitial(provider) { return (PROVIDER_LABELS[provider] || provider).charAt(0).toUpperCase() }
function splitTags(tags) { return (tags || '').split(',').map(t => t.trim()).filter(Boolean) }

onMounted(async () => {
  try {
    const data = await gatewayApi.listModelCatalog()
    models.value = (data.data || []).map(m => ({
      ...m,
      id: m.model,
      input_fmt: (m.input_price || 0).toFixed(2),
      output_fmt: (m.output_price || 0).toFixed(2),
      per_use_fmt: (m.per_use || 0).toFixed(2),
      per_use: m.per_use || 0,
    }))
  } catch (e) { /* silent */ }
})
</script>

<style scoped>
.model-filter-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.model-tab {
  padding: 6px 16px; border-radius: 20px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text-secondary); font-size: 13px; cursor: pointer;
  transition: all 0.15s;
}
.model-tab:hover { border-color: var(--primary); color: var(--primary); }
.model-tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
.model-search {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid var(--border); font-size: 13px;
  width: 200px; outline: none; background: var(--surface); color: var(--text);
}
.model-search:focus { border-color: var(--primary); }
.section-heading { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 12px; }
.featured-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.featured-card {
  border-radius: var(--radius-lg); border: 1px solid var(--border-light);
  overflow: hidden; cursor: pointer; background: var(--surface);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.featured-card:hover { box-shadow: 0 4px 20px rgba(79,110,247,0.15); border-color: var(--primary); }
.featured-banner {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 24px; color: #fff;
}
.banner-purple { background: linear-gradient(135deg,#7c3aed,#4f46e5); }
.banner-mint   { background: linear-gradient(135deg,#059669,#0891b2); }
.banner-blue   { background: linear-gradient(135deg,#2563eb,#4f46e5); }
.banner-yellow { background: linear-gradient(135deg,#d97706,#dc2626); }
.banner-orange { background: linear-gradient(135deg,#ea580c,#d97706); }
.banner-pink   { background: linear-gradient(135deg,#db2777,#7c3aed); }
.featured-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; flex-shrink: 0;
}
.featured-name { font-size: 16px; font-weight: 700; }
.featured-sub  { font-size: 12px; opacity: 0.8; margin-top: 2px; }
.featured-body { padding: 16px 20px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.mtag {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: var(--primary-light); color: var(--primary);
}
.mdesc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 12px; }
.price-row { display: flex; gap: 6px; flex-wrap: wrap; }
.pchip {
  font-size: 11px; padding: 3px 8px; border-radius: 10px;
  background: #f1f5f9; color: var(--text-secondary); border: 1px solid var(--border-light);
}
.pchip--amber { background: #fef3c7; color: #b45309; border-color: #fde68a; }
.model-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}
@media (max-width: 900px) { .model-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .featured-grid { grid-template-columns: 1fr; } }
.model-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px; cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
  display: flex; flex-direction: column; gap: 8px; min-height: 130px;
}
.model-card:hover { box-shadow: 0 4px 16px rgba(79,110,247,0.12); border-color: var(--primary); }
.mc-header { display: flex; align-items: center; gap: 10px; }
.mc-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.icon-purple { background: linear-gradient(135deg,#7c3aed,#4f46e5); }
.icon-mint   { background: linear-gradient(135deg,#059669,#0891b2); }
.icon-blue   { background: linear-gradient(135deg,#2563eb,#4f46e5); }
.icon-yellow { background: linear-gradient(135deg,#d97706,#dc2626); }
.icon-orange { background: linear-gradient(135deg,#ea580c,#d97706); }
.icon-pink   { background: linear-gradient(135deg,#db2777,#7c3aed); }
.mc-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mc-provider { font-size: 11px; color: var(--text-muted); }
.mc-desc {
  font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  flex: 1;
}
.model-empty { text-align: center; padding: 60px 0; color: var(--text-muted); font-size: 14px; }
</style>
