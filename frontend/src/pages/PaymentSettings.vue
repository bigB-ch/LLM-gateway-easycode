<template>
  <div>
    <n-h3>支付配置</n-h3>

    <n-tabs type="line" animated>
      <n-tab-pane name="alipay" tab="支付宝">
        <n-alert :bordered="true" type="info" style="margin-bottom:16px;font-size:13px">
          需要 支付宝商家中心 — 电脑网站支付 的凭证。
          <a href="https://open.alipay.com/" target="_blank" style="color:var(--primary)">前往支付宝开放平台 &rarr;</a>
        </n-alert>

        <n-form :model="form" label-placement="left" label-width="160px">
          <n-form-item label="App ID">
            <n-input v-model:value="form.app_id" placeholder="支付宝应用 App ID" />
          </n-form-item>

          <n-form-item label="应用私钥">
            <n-input
              v-model:value="form.private_key"
              type="textarea"
              :rows="5"
              placeholder="RSA2 私钥，-----BEGIN RSA PRIVATE KEY----- ..."
              style="font-family: monospace; font-size: 12px"
            />
          </n-form-item>

          <n-form-item label="支付宝公钥">
            <n-input
              v-model:value="form.alipay_public_key"
              type="textarea"
              :rows="3"
              placeholder="支付宝公钥，-----BEGIN PUBLIC KEY----- ..."
              style="font-family: monospace; font-size: 12px"
            />
          </n-form-item>

          <n-form-item label="固定收款二维码">
            <n-input v-model:value="form.alipay_qr_url" placeholder="https://example.com/alipay-qr.png" />
            <template #feedback>
              已废弃 — 支付宝现使用电脑网站支付（跳转页面），此字段不再生效
            </template>
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="wechat" tab="微信支付">
        <n-alert :bordered="true" type="warning" style="margin-bottom:16px;font-size:13px">
          微信支付 Native 集成需要使用微信支付商户号，暂未完整对接。
        </n-alert>

        <n-form :model="form" label-placement="left" label-width="160px">
          <n-form-item label="固定收款二维码（微信）">
            <n-input v-model:value="form.wechat_qr_url" placeholder="https://example.com/wechat-qr.png" />
            <template #feedback>
              微信支付固定二维码，用户付款后通知管理员审核到账
            </template>
          </n-form-item>
        </n-form>
      </n-tab-pane>
    </n-tabs>

    <div style="margin-top:24px;display:flex;gap:12px">
      <n-button type="primary" :loading="saving" @click="saveConfig">
        {{ saving ? '保存中...' : '保存配置' }}
      </n-button>
      <n-button v-if="testResult !== null" :type="testResult ? 'success' : 'error'" size="small" disabled>
        {{ testResult ? '支付宝连接正常' : '验证失败，请检查凭证' }}
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { NAlert, NButton, NForm, NFormItem, NH3, NInput, NTabPane, NTabs } from 'naive-ui'
import { api } from '../api'

const message = useMessage()

const form = ref({
  app_id: '',
  private_key: '',
  alipay_public_key: '',
  alipay_qr_url: '',
  wechat_qr_url: '',
})

const saving = ref(false)
const testResult = ref(null)

onMounted(async () => {
  try {
    const cfg = await api.getPaymentConfig()
    if (cfg && cfg.app_id) form.value.app_id = cfg.app_id
    if (cfg && cfg.private_key) form.value.private_key = cfg.private_key
    if (cfg && cfg.alipay_public_key) form.value.alipay_public_key = cfg.alipay_public_key
    if (cfg && cfg.alipay_qr_url) form.value.alipay_qr_url = cfg.alipay_qr_url
    if (cfg && cfg.wechat_qr_url) form.value.wechat_qr_url = cfg.wechat_qr_url
  } catch (e) { /* no config yet */ }
})

async function saveConfig() {
  saving.value = true
  try {
    await api.savePaymentConfig(form.value)
    message.success('支付配置已保存')
  } catch (e) {
    message.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>
