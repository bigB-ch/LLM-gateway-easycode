<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">{{ t('supplierManagement') }}</n-h1>
      <n-button type="primary" @click="toggleForm">{{ showForm ? t('cancel') : t('addSupplier') }}</n-button>
    </n-space>

    <n-card v-if="showForm" :bordered="true" size="small" style="margin-bottom:24px">
      <n-space align="flex-end" wrap :size="16">
        <n-form-item :label="t('supplier')" style="min-width:160px">
          <n-select v-model:value="formProvider" :options="providerOptions" :placeholder="t('selectSupplier')" />
        </n-form-item>
        <n-form-item label="API Key" style="flex:1;min-width:200px">
          <n-input v-model:value="formApiKey" placeholder="sk-..." />
        </n-form-item>
        <n-form-item label="Base URL" style="flex:1;min-width:200px">
          <n-input v-model:value="formBaseUrl" placeholder="https://api.openai.com/v1" />
        </n-form-item>
        <n-form-item label="余额 ($)" style="width:120px">
          <n-input-number v-model:value="formBalance" :min="0" :step="0.01" placeholder="0.00" style="width:100%" />
        </n-form-item>
        <n-button type="primary" :loading="saving" @click="saveSupplier">{{ saving ? '保存中...' : '保存' }}</n-button>
      </n-space>
    </n-card>

    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="suppliers" :bordered="false" :min-height="80" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  NCard, NDataTable, NH1, NButton, NInput, NInputNumber, NSelect,
  NSpace, NFormItem, NTag, NPopconfirm, NText,
} from 'naive-ui'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

const suppliers = ref([])
const healthResults = ref({})
const balanceLoading = ref({})
const showForm = ref(false)
const formProvider = ref('')
const formApiKey = ref('')
const formBaseUrl = ref('')
const formBalance = ref(0)
const saving = ref(false)

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '阿里巴巴 / Qwen', value: 'qwen' },
  { label: '智谱 / GLM', value: 'zhipu' },
  { label: 'Moonshot / Kimi', value: 'moonshot' },
  { label: '字节跳动 / 豆包', value: 'doubao' },
  { label: 'MiniMax', value: 'minimax' },
  { label: '快手可灵 / Kling', value: 'kling' },
]

function resetForm() { formProvider.value = ''; formApiKey.value = ''; formBaseUrl.value = ''; formBalance.value = 0 }
function toggleForm() { showForm.value = !showForm.value; if (showForm.value) resetForm() }

const tableColumns = [
  { title: t('supplier'), key: 'provider', render: (row) => h('strong', row.provider) },
  { title: 'API Key', key: 'api_key_masked', render: (row) => h('code', { style: 'font-size:12px' }, row.api_key_masked) },
  { title: 'Base URL', key: 'base_url' },
  {
    title: t('balance'), key: 'balance',
    render: (row) => {
      if (balanceLoading.value[row.provider]) return h('span', { style: 'color:#888;font-size:12px' }, '查询中...')
      return h('div', { style: 'display:flex;align-items:center;gap:8px' }, [
        h('span', { style: { color: (row.balance || 0) <= 0 ? '#dc2626' : '#059669', fontWeight: '500' } },
          row.balance > 0 ? '$' + row.balance.toFixed(2) : row.balance === 0 ? '$0.00' : '-'),
        h(NButton, { size: 'tiny', onClick: () => checkBalance(row.provider) }, { default: () => t('checkBalance') }),
      ])
    },
  },
  {
    title: t('status'), key: 'health',
    render: (row) => {
      if (healthResults.value[row.provider]?.checking) return h(NTag, { type: 'default', size: 'small' }, { default: () => '检测中' })
      if (healthResults.value[row.provider]?.checked) return h(NTag, { type: healthResults.value[row.provider].healthy ? 'success' : 'error', size: 'small' },
        { default: () => healthResults.value[row.provider].healthy ? t('healthy') : t('abnormal') })
      return h(NTag, { type: 'default', size: 'small' }, { default: () => '-' })
    },
  },
  {
    title: t('operation'), key: 'actions',
    render: (row) => h('div', { style: 'display:flex;gap:4px' }, [
      h(NButton, { size: 'small', onClick: () => editSupplier(row) }, { default: () => t('edit') }),
      h(NButton, { size: 'small', onClick: () => checkHealth(row.provider) }, { default: () => t('healthCheck') }),
      h(NPopconfirm, {
        onPositiveClick: () => removeSupplier(row.provider),
      }, {
        trigger: () => h(NButton, { size: 'small', color: '#dc2626' }, { default: () => t('delete') }),
        default: () => `确定删除供应商 "${row.provider}"？`,
      }),
    ]),
  },
]

async function loadSuppliers() {
  try { suppliers.value = await gatewayApi.listSuppliers() } catch (e) { /* */ }
}
onMounted(loadSuppliers)

async function saveSupplier() {
  if (!formProvider.value || !formApiKey.value || !formBaseUrl.value) return
  saving.value = true
  try {
    await gatewayApi.upsertSupplier(formProvider.value, formApiKey.value, formBaseUrl.value, formBalance.value || 0)
    formProvider.value = ''; formApiKey.value = ''; formBaseUrl.value = ''; formBalance.value = 0; showForm.value = false
    await loadSuppliers()
    message.success('保存成功')
  } catch (e) { message.error('保存失败: ' + e.message) }
  finally { saving.value = false }
}

function editSupplier(s) {
  formProvider.value = s.provider; formApiKey.value = ''; formBaseUrl.value = s.base_url
  formBalance.value = s.balance || 0; showForm.value = true
}

async function removeSupplier(provider) {
  try { await gatewayApi.deleteSupplier(provider); await loadSuppliers(); message.success('已删除') }
  catch (e) { message.error('删除失败: ' + e.message) }
}

async function checkBalance(provider) {
  balanceLoading.value[provider] = true
  try {
    const res = await gatewayApi.checkBalance(provider)
    if (res.balance != null) {
      const s = suppliers.value.find(x => x.provider === provider)
      if (s) s.balance = res.balance
    } else {
      message.warning(res.error || '暂不支持该供应商的余额查询')
    }
  } catch (e) { message.error('查询失败: ' + e.message) }
  finally { balanceLoading.value[provider] = false }
}

async function checkHealth(provider) {
  healthResults.value[provider] = { checking: true, checked: false, healthy: false }
  try {
    const res = await gatewayApi.healthCheck(provider)
    healthResults.value[provider] = { checking: false, checked: true, healthy: res.healthy }
    setTimeout(() => {
      if (healthResults.value[provider]) healthResults.value[provider].checked = false
    }, 5000)
  } catch (e) { healthResults.value[provider] = { checking: false, checked: true, healthy: false } }
}
</script>
