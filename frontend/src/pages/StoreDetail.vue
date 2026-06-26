<template>
  <div class="detail-page" v-if="product">
    <div class="detail-header">
      <button class="back-btn" @click="$router.back()">&larr; 返回</button>
    </div>

    <div class="detail-layout">
      <div class="detail-main">
        <div class="detail-thumb" :style="product.thumbnail_url ? { backgroundImage: `url(${product.thumbnail_url})` } : {}"></div>

        <h1 class="detail-title">{{ product.name }}</h1>
        <p class="detail-desc">{{ product.description }}</p>

        <div class="detail-meta">
          <div class="meta-item" v-if="product.version"><label>版本</label><span>v{{ product.version }}</span></div>
          <div class="meta-item" v-if="product.file_size"><label>大小</label><span>{{ formatSize(product.file_size) }}</span></div>
          <div class="meta-item" v-if="product.system_requirements"><label>系统要求</label><span>{{ product.system_requirements }}</span></div>
          <div class="meta-item"><label>分类</label><span>{{ catLabel }}</span></div>
        </div>
      </div>

      <div class="detail-sidebar">
        <div class="sidebar-card">
          <div class="price-tag">¥{{ product.price_yuan }}</div>

          <button v-if="product.purchased" class="action-btn downloaded" @click="goOrders">已购买 — 前往下载</button>

          <button v-else class="action-btn" :disabled="ordering" @click="startOrder">
            {{ ordering ? '处理中...' : '立即购买' }}
          </button>

          <div class="qr-section" v-if="qrCode">
            <p class="qr-hint">请使用支付宝扫码支付</p>
            <img :src="qrCode" class="qr-img" />
            <p class="qr-status">{{ polling ? '等待支付...' : '' }}</p>
          </div>

          <div class="order-success" v-if="paid">
            <p>支付成功！</p>
            <button class="action-btn downloaded" @click="goOrders">前往下载</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="!loading" class="not-found">商品不存在</div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const product = ref(null)
const loading = ref(true)
const ordering = ref(false)
const qrCode = ref('')
const orderId = ref('')
const polling = ref(false)
const paid = ref(false)

const categories = { agent: 'Agent', dev_tool: '开发工具', env_pack: '环境包' }
const catLabel = computed(() => categories[product.value?.category] || product.value?.category)

function formatSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / 1024 / 1024
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(0)} MB`
}

function goOrders() { router.push('/orders') }

let pollTimer = null

async function startOrder() {
  ordering.value = true
  try {
    const res = await api.createOrder(product.value.id, 'alipay')
    qrCode.value = res.qr_code
    orderId.value = res.order_id
    ordering.value = false
    startPolling()
  } catch (e) {
    ordering.value = false
    alert('下单失败：' + e.message)
  }
}

async function startPolling() {
  polling.value = true
  const poll = async () => {
    if (!orderId.value) return
    try {
      const res = await api.queryOrder(orderId.value)
      if (res.paid) {
        paid.value = true
        polling.value = false
        qrCode.value = ''
        product.value.purchased = true
        return
      }
    } catch (_) {}
    pollTimer = setTimeout(poll, 2000)
  }
  pollTimer = setTimeout(poll, 2000)
}

onMounted(async () => {
  try {
    const res = await api.getProduct(route.params.id)
    product.value = res
  } catch (_) { product.value = null }
  loading.value = false
})

onUnmounted(() => { if (pollTimer) clearTimeout(pollTimer) })
</script>

<style scoped>
.detail-page { max-width: 1000px; margin: 0 auto; padding: 24px; }
.detail-header { margin-bottom: 20px; }
.back-btn { background: none; border: 1px solid var(--border); padding: 6px 16px; border-radius: 8px; cursor: pointer; color: var(--text); font-size: 0.85rem; }
.back-btn:hover { border-color: var(--primary); color: var(--primary); }
.detail-layout { display: flex; gap: 32px; }
.detail-main { flex: 1; }
.detail-thumb { height: 200px; border-radius: 12px; background: linear-gradient(135deg, #f0f2f5, #e5e7eb); background-size: cover; background-position: center; margin-bottom: 20px; }
.detail-title { margin: 0 0 8px; font-size: 1.5rem; }
.detail-desc { color: var(--text-muted); font-size: 0.9rem; margin: 0 0 20px; line-height: 1.6; }
.detail-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-item label { font-size: 0.75rem; color: var(--text-muted); }
.meta-item span { font-size: 0.9rem; }
.detail-sidebar { width: 280px; flex-shrink: 0; }
.sidebar-card { background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 24px; position: sticky; top: 80px; text-align: center; }
.price-tag { font-size: 2rem; font-weight: 800; color: var(--primary); margin-bottom: 20px; }
.action-btn { width: 100%; padding: 12px; border: none; border-radius: 10px; background: var(--primary); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.action-btn.downloaded { background: var(--success, #34d399); }
.qr-section { margin-top: 20px; }
.qr-hint { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px; }
.qr-img { width: 180px; height: 180px; }
.qr-status { font-size: 0.8rem; color: var(--primary); margin-top: 8px; }
.order-success { margin-top: 20px; }
.order-success p { font-weight: 600; color: var(--success, #34d399); margin-bottom: 12px; }
.loading, .not-found { text-align: center; padding: 80px 0; color: var(--text-muted); }
@media (max-width: 700px) { .detail-layout { flex-direction: column; } .detail-sidebar { width: 100%; } }
</style>
