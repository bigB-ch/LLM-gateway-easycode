<template>
  <div class="store-page">
    <div class="page-header">
      <h2>AI 商店</h2>
      <div class="filter-bar">
        <button
          v-for="cat in categories"
          :key="cat.key"
          :class="['filter-btn', { active: activeCategory === cat.key }]"
          @click="activeCategory = cat.key; loadProducts()"
        >{{ cat.label }}</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!products.length" class="empty">暂无商品</div>
    <div v-else class="product-grid">
      <div v-for="p in products" :key="p.id" class="product-card" @click="goDetail(p.id)">
        <div class="pc-thumb" :style="p.thumbnail_url ? { backgroundImage: `url(${p.thumbnail_url})` } : {}">
          <div class="pc-cat-tag">{{ getCatLabel(p.category) }}</div>
        </div>
        <div class="pc-body">
          <h3 class="pc-name">{{ p.name }}</h3>
          <p class="pc-desc">{{ p.description }}</p>
          <div class="pc-meta" v-if="p.version || p.file_size">
            <span v-if="p.version">v{{ p.version }}</span>
            <span v-if="p.file_size">{{ formatSize(p.file_size) }}</span>
          </div>
          <div class="pc-footer">
            <span class="pc-price">¥{{ p.price_yuan }}</span>
            <span class="pc-btn" :class="{ purchased: p.purchased }">
              {{ p.purchased ? '已购买' : '购买' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const products = ref([])
const loading = ref(true)
const activeCategory = ref('')

const categories = [
  { key: '', label: '全部' },
  { key: 'agent', label: 'Agent' },
  { key: 'dev_tool', label: '开发工具' },
  { key: 'env_pack', label: '环境包' },
]

function getCatLabel(key) {
  const c = categories.find(c => c.key === key)
  return c ? c.label : key
}

function formatSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / 1024 / 1024
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(0)} MB`
}

function goDetail(id) {
  router.push(`/store/${id}`)
}

async function loadProducts() {
  loading.value = true
  try {
    const res = await api.listProducts(activeCategory.value || undefined)
    products.value = res.items || []
  } catch (_) {
    products.value = []
  }
  loading.value = false
}

onMounted(loadProducts)
</script>

<style scoped>
.store-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 1.4rem; }
.filter-bar { display: flex; gap: 8px; }
.filter-btn { padding: 6px 16px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--text); font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
.filter-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.filter-btn:hover:not(.active) { border-color: var(--primary); color: var(--primary); }
.loading, .empty { text-align: center; padding: 80px 0; color: var(--text-muted); }
.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.product-card { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--bg); cursor: pointer; transition: all 0.2s; }
.product-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-color: var(--primary); }
.pc-thumb { height: 140px; background: linear-gradient(135deg, #f0f2f5, #e5e7eb); background-size: cover; background-position: center; position: relative; }
.pc-cat-tag { position: absolute; top: 10px; left: 10px; padding: 2px 10px; border-radius: 10px; background: rgba(0,0,0,0.5); color: #fff; font-size: 0.75rem; }
.pc-body { padding: 14px 16px 16px; }
.pc-name { margin: 0 0 6px; font-size: 1rem; font-weight: 600; }
.pc-desc { margin: 0; font-size: 0.82rem; color: var(--text-muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.pc-meta { display: flex; gap: 12px; margin-top: 10px; font-size: 0.75rem; color: var(--text-muted); }
.pc-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-light, #eee); }
.pc-price { font-size: 1.15rem; font-weight: 700; color: var(--primary); }
.pc-btn { padding: 5px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 500; background: var(--primary); color: #fff; }
.pc-btn.purchased { background: var(--success, #34d399); }
@media (max-width: 600px) { .page-header { flex-direction: column; align-items: flex-start; gap: 12px; } }
</style>
