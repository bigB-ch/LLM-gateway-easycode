<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('supplierManagement') }}</h1>
      <button class="btn btn-primary" @click="showForm = !showForm">{{ showForm ? t('cancel') : t('addSupplier') }}</button>
    </div>

    <div v-if="showForm" class="card card-padded mb-24">
      <div style="display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap">
        <div style="min-width:160px">
          <label class="form-label">{{ t('supplier') }}</label>
          <select v-model="formProvider" class="form-select">
            <option value="">{{ t('selectSupplier') }}</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="deepseek">DeepSeek</option>
            <option value="qwen">阿里巴巴 / Qwen</option>
            <option value="zhipu">智谱 / GLM</option>
            <option value="moonshot">Moonshot / Kimi</option>
            <option value="doubao">字节跳动 / 豆包</option>
            <option value="minimax">MiniMax</option>
            <option value="kling">快手可灵 / Kling</option>
          </select>
        </div>
        <div style="flex:1;min-width:200px">
          <label class="form-label">API Key</label>
          <input v-model="formApiKey" class="form-input" placeholder="sk-..." />
        </div>
        <div style="flex:1;min-width:200px">
          <label class="form-label">Base URL</label>
          <input v-model="formBaseUrl" class="form-input" placeholder="https://api.openai.com/v1" />
        </div>
        <div style="width:120px">
          <label class="form-label">余额 ($)</label>
          <input v-model.number="formBalance" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
        </div>
        <button class="btn btn-primary" @click="saveSupplier" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr><th>{{ t('supplier') }}</th><th>API Key</th><th>Base URL</th><th>{{ t('balance') }}</th><th>{{ t('status') }}</th><th>{{ t('operation') }}</th></tr>
          </thead>
          <tbody>
            <tr v-if="suppliers.length === 0">
              <td colspan="6"><div class="empty-state"><div class="empty-state-icon">&#x2699;&#xFE0F;</div><div class="empty-state-text">{{ t('noSuppliers') }}</div></div></td>
            </tr>
            <tr v-for="s in suppliers" :key="s.provider">
              <td><strong>{{ s.provider }}</strong></td>
              <td><span class="key-masked">{{ s.api_key_masked }}</span></td>
              <td class="text-secondary" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block">{{ s.base_url }}</td>
              <td>
                <span v-if="balanceLoading[s.provider]" style="color:#888;font-size:12px">{{ t('query') }}中...</span>
                <span v-else :style="{color: (s.balance || 0) <= 0 ? '#dc2626' : '#059669',fontWeight:'500'}">
                  {{ s.balance > 0 ? '$' + s.balance.toFixed(2) : (s.balance === 0 ? '$0.00' : '-') }}
                </span>
                <button class="btn btn-outline btn-xs" @click="checkBalance(s.provider)" style="margin-left:8px">{{ t('checkBalance') }}</button>
              </td>
              <td>
                <span v-if="healthResults[s.provider]?.checking" class="badge badge-default">检测中</span>
                <span v-else-if="healthResults[s.provider]?.checked" :class="'badge ' + (healthResults[s.provider].healthy ? 'badge-success' : 'badge-danger')">{{ healthResults[s.provider].healthy ? t('healthy') : t('abnormal') }}</span>
                <span v-else class="badge badge-default">-</span>
              </td>
              <td>
                <button class="btn btn-outline btn-sm" @click="editSupplier(s)" style="margin-right:4px">{{ t('edit') }}</button>
                <button class="btn btn-outline btn-sm" @click="checkHealth(s.provider)" style="margin-right:4px">{{ t('healthCheck') }}</button>
                <button class="btn btn-danger btn-sm" @click="removeSupplier(s.provider)">{{ t('delete') }}</button>
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
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()

const suppliers = ref([])
const healthResults = ref({})
const balanceLoading = ref({})
const showForm = ref(false)
const formProvider = ref('')
const formApiKey = ref('')
const formBaseUrl = ref('')
const formBalance = ref(0)
const saving = ref(false)

async function loadSuppliers() { try { suppliers.value = await gatewayApi.listSuppliers() } catch (e) { /* */ } }
onMounted(loadSuppliers)

async function saveSupplier() {
  if (!formProvider.value || !formApiKey.value || !formBaseUrl.value) return
  saving.value = true
  try {
    await gatewayApi.upsertSupplier(formProvider.value, formApiKey.value, formBaseUrl.value, formBalance.value || 0)
    formProvider.value = ''; formApiKey.value = ''; formBaseUrl.value = ''; formBalance.value = 0; showForm.value = false
    await loadSuppliers()
  } catch (e) { alert('保存失败: ' + e.message) } finally { saving.value = false }
}

function editSupplier(s) { formProvider.value = s.provider; formApiKey.value = ''; formBaseUrl.value = s.base_url; formBalance.value = s.balance || 0; showForm.value = true }

async function removeSupplier(provider) {
  if (!confirm(`确定删除供应商 "${provider}"？`)) return
  try { await gatewayApi.deleteSupplier(provider); await loadSuppliers() } catch (e) { alert('删除失败: ' + e.message) }
}

async function checkBalance(provider) {
  balanceLoading.value[provider] = true
  try {
    const res = await gatewayApi.checkBalance(provider)
    if (res.balance != null) {
      const s = suppliers.value.find(x => x.provider === provider)
      if (s) s.balance = res.balance
    } else {
      alert(res.error || '暂不支持该供应商的余额查询')
    }
  } catch (e) { alert('查询失败: ' + e.message) }
  finally { balanceLoading.value[provider] = false }
}

async function checkHealth(provider) {
  healthResults.value[provider] = { checking: true, checked: false, healthy: false }
  try {
    const res = await gatewayApi.healthCheck(provider)
    healthResults.value[provider] = { checking: false, checked: true, healthy: res.healthy }
    setTimeout(() => { if (healthResults.value[provider]) healthResults.value[provider].checked = false }, 5000)
  } catch (e) { healthResults.value[provider] = { checking: false, checked: true, healthy: false } }
}
</script>
