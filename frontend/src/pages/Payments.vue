<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">支付审核</h1>
      <button class="btn btn-outline btn-sm" @click="loadPayments">{{ t('refresh') }}</button>
    </div>

    <!-- Alipay Config -->
    <div class="card card-padded mb-16">
      <h3 class="section-title mb-12">支付宝商户配置</h3>
      <p style="font-size:12px;color:var(--text-secondary);margin-bottom:12px">
        需要开通支付宝当面付（F2F）。前往 open.alipay.com 创建应用获取以下参数。
        未配置时使用手动审核模式。
      </p>
      <div style="display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;gap:16px;flex-wrap:wrap">
          <div style="flex:1;min-width:200px">
            <label class="form-label">App ID</label>
            <input v-model="alipayAppId" class="form-input" placeholder="2021xxxxxxxxxxxx" />
          </div>
          <div style="flex:1;min-width:200px">
            <label class="form-label">支付宝公钥</label>
            <input v-model="alipayPublicKey" class="form-input" placeholder="MIIBIjANBgkq..." />
          </div>
        </div>
        <div>
          <label class="form-label">应用私钥（RSA2）</label>
          <textarea v-model="alipayPrivateKey" class="form-input" rows="4" placeholder="-----BEGIN RSA PRIVATE KEY-----"></textarea>
        </div>
        <div style="align-self:flex-start">
          <button class="btn btn-primary" @click="saveAlipayConfig" :disabled="savingQr">{{ savingQr ? '保存中...' : '保存支付宝配置' }}</button>
        </div>
      </div>
      <div v-if="qrMsg" :class="qrMsg.includes('失败')?'alert alert-error':'alert alert-success'" style="font-size:12px;margin-top:8px">{{ qrMsg }}</div>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr><th>时间</th><th>用户</th><th>金额</th><th>方式</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-if="payments.length === 0">
              <td colspan="6"><div class="empty-state" style="padding:40px"><div class="empty-state-icon">&#x2705;</div><div class="empty-state-text">暂无待审核支付</div></div></td>
            </tr>
            <tr v-for="p in payments" :key="p.id">
              <td class="text-muted" style="font-size:12px;white-space:nowrap">{{ fmtTime(p.created_at) }}</td>
              <td>
                <div style="font-weight:500">{{ p.username }}</div>
                <div class="text-muted" style="font-size:11px">{{ p.email }}</div>
              </td>
              <td style="font-weight:700;color:var(--primary);font-size:15px">&yen;{{ p.amount_yuan }}</td>
              <td><span class="badge" :class="p.method==='alipay'?'badge-primary':'badge-success'" style="font-size:10px">{{ p.method === 'alipay' ? '支付宝' : p.method === 'wechat' ? '微信' : p.method }}</span></td>
              <td><span class="badge badge-warning" style="font-size:10px">待审核</span></td>
              <td>
                <button class="btn btn-primary btn-sm" @click="verify(p.id, true)" style="margin-right:4px">通过</button>
                <button class="btn btn-danger btn-sm" @click="verify(p.id, false)">拒绝</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const payments = ref([])
const alipayAppId = ref(''); const alipayPublicKey = ref(''); const alipayPrivateKey = ref('')
const savingQr = ref(false); const qrMsg = ref('')

onMounted(() => { loadPayments(); loadAlipayConfig() })

async function loadAlipayConfig() {
  try { const cfg = await api.getPaymentConfig(); alipayAppId.value = cfg.app_id || ''; alipayPublicKey.value = cfg.alipay_public_key || ''; alipayPrivateKey.value = cfg.private_key || '' } catch(e){}
}
async function saveAlipayConfig() {
  savingQr.value = true; qrMsg.value = ''
  try {
    await api.savePaymentConfig({
      app_id: alipayAppId.value, alipay_public_key: alipayPublicKey.value, private_key: alipayPrivateKey.value,
    })
    qrMsg.value = 'Alipay config saved'
  } catch(e) { qrMsg.value = 'Save failed: ' + e.message } finally { savingQr.value = false }
}
async function loadPayments() {
  try { payments.value = (await api.getPendingPayments()).items || [] } catch(e){}
}

async function verify(id, approved) {
  const label = approved ? '通过' : '拒绝'
  if (!confirm(`确定${label}这笔支付？`)) return
  try {
    await api.verifyPayment(id, approved)
    loadPayments()
  } catch(e) { alert('操作失败: ' + e.message) }
}

async function loadQrConfig() {
  try { const cfg = await api.getPaymentConfig(); qrAlipay.value = cfg.alipay_qr_url || ''; qrWechat.value = cfg.wechat_qr_url || '' } catch(e){}
}
async function saveQrConfig() {
  savingQr.value = true; qrMsg.value = ''
  try {
    await api.savePaymentConfig(qrAlipay.value, qrWechat.value)
    qrMsg.value = '保存成功'
  } catch(e) { qrMsg.value = '保存失败: ' + e.message } finally { savingQr.value = false }
}

function fmtTime(iso) {
  return iso ? new Date(iso).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}) : '-'
}
</script>
