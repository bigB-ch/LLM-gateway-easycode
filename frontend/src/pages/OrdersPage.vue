<template>
  <div class="orders-page">
    <h2>我的订单</h2>

    <div v-if="loading" class="status-text">加载中...</div>
    <div v-else-if="!orders.length" class="status-text empty">暂无订单</div>

    <div v-else class="order-list">
      <div v-for="o in orders" :key="o.id" class="order-card">
        <div class="order-info">
          <div class="order-product">
            <div class="op-thumb" :style="o.product_thumbnail ? { backgroundImage: `url(${o.product_thumbnail})` } : {}"></div>
            <div>
              <div class="op-name">{{ o.product_name }}</div>
              <div class="op-meta">
                <span>¥{{ o.amount_yuan }}</span>
                <span>{{ o.method === 'alipay' ? '支付宝' : '微信' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="order-status">
          <span :class="o.status === 'paid' ? 'badge-paid' : 'badge-pending'">
            {{ o.status === 'paid' ? '已支付' : '待支付' }}
          </span>
        </div>
        <div class="order-action">
          <button v-if="o.status === 'paid'" class="dl-btn" @click="downloadOrder(o)">下载</button>
          <button v-else class="retry-btn" @click="retryPayment(o)">继续支付</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const orders = ref([])
const loading = ref(true)

async function loadOrders() {
  loading.value = true
  try {
    const res = await api.listOrders()
    orders.value = res.items || []
  } catch (_) { orders.value = [] }
  loading.value = false
}

async function downloadOrder(order) {
  try {
    const res = await api.getDownloadUrl(order.id)
    window.location.href = res.download_url
  } catch (e) {
    alert('下载失败：' + e.message)
  }
}

async function retryPayment(order) {
  try {
    await api.createOrder(order.product_id, 'alipay')
    window.location.href = `/store/${order.product_id}`
  } catch (e) {
    alert('操作失败：' + e.message)
  }
}

onMounted(loadOrders)
</script>

<style scoped>
.orders-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.orders-page h2 { margin: 0 0 24px; }
.status-text { text-align: center; padding: 60px 0; color: var(--text-muted); }
.order-list { display: flex; flex-direction: column; gap: 12px; }
.order-card { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg); }
.order-info { flex: 1; }
.order-product { display: flex; align-items: center; gap: 12px; }
.op-thumb { width: 48px; height: 48px; border-radius: 8px; background: linear-gradient(135deg, #f0f2f5, #e5e7eb); background-size: cover; background-position: center; flex-shrink: 0; }
.op-name { font-weight: 600; font-size: 0.95rem; }
.op-meta { display: flex; gap: 10px; font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }
.order-status { margin: 0 20px; }
.badge-paid { padding: 3px 12px; border-radius: 10px; font-size: 0.78rem; background: #d1fae5; color: #065f46; }
.badge-pending { padding: 3px 12px; border-radius: 10px; font-size: 0.78rem; background: #fef3c7; color: #92400e; }
.dl-btn, .retry-btn { padding: 8px 20px; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 500; cursor: pointer; }
.dl-btn { background: var(--primary); color: #fff; }
.retry-btn { background: #fef3c7; color: #92400e; }
</style>
