<template>
  <div>
    <!-- Summary cards -->
    <div class="key-summary-grid">
      <div class="key-summary-card" style="background:var(--card-blue-bg);border-left:3px solid var(--card-blue-accent)">
        <div class="ksc-label">Key 总数</div>
        <div class="ksc-value">{{ keys.length }}</div>
      </div>
      <div class="key-summary-card" style="background:var(--card-green-bg);border-left:3px solid var(--card-green-accent)">
        <div class="ksc-label">有效 Key</div>
        <div class="ksc-value" style="color:var(--status-active)">{{ activeCount }}</div>
      </div>
      <div class="key-summary-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
        <div class="ksc-label">本月调用量</div>
        <div class="ksc-value">{{ monthCalls.toLocaleString() }}</div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="key-toolbar">
      <n-button type="primary" size="small" @click="showCreate = true">+ 新建 API Key</n-button>
      <n-input v-model:value="searchName" placeholder="搜索名称" clearable size="small" style="width:150px" @keyup.enter="doSearch" />
      <n-input v-model:value="searchKey" placeholder="Key 前缀" clearable size="small" style="width:150px" @keyup.enter="doSearch" />
      <n-select v-model:value="filterStatus" :options="statusOptions" size="small" style="width:100px" />
      <div style="flex:1" />
      <template v-if="selected.length">
        <n-popconfirm @positive-click="batchRevoke">
          <template #trigger>
            <n-button size="small" style="color:var(--status-revoked);border-color:var(--status-revoked)">
              批量撤销 ({{ selected.length }})
            </n-button>
          </template>
          确定撤销 {{ selected.length }} 个令牌？
        </n-popconfirm>
        <n-popconfirm @positive-click="batchDelete">
          <template #trigger>
            <n-button size="small" style="color:var(--status-revoked);border-color:var(--status-revoked)">
              批量删除 ({{ selected.length }})
            </n-button>
          </template>
          确定永久删除 {{ selected.length }} 个令牌？
        </n-popconfirm>
      </template>
    </div>

    <!-- Table -->
    <div class="key-table-card">
      <n-data-table
        v-if="filteredKeys.length"
        :columns="tableColumns"
        :data="filteredKeys"
        :row-key="row => row.id"
        :checked-row-keys="selected"
        :single-line="false"
        :row-class-name="row => row.status === 'revoked' ? 'row-revoked' : ''"
        size="small"
        @update:checked-row-keys="selected = $event"
      />
      <n-empty v-else description="暂无 API Key" style="padding:48px 0">
        <template #extra>
          <n-button size="small" @click="showCreate = true">创建第一个 Key</n-button>
        </template>
      </n-empty>
      <div v-if="filteredKeys.length" class="key-table-footer">
        共 {{ filteredKeys.length }} 条
      </div>
    </div>

    <!-- API Info card -->
    <div class="key-api-card" style="background:var(--card-purple-bg);border-left:3px solid var(--card-purple-accent)">
      <div class="key-api-title">接入信息</div>
      <div class="key-api-row">
        <span class="key-api-label">Base URL</span>
        <code class="key-api-code">https://easycode.uno/v1</code>
      </div>
      <div class="key-api-row">
        <span class="key-api-label">Auth 方式</span>
        <code class="key-api-code">Authorization: Bearer &lt;API Key&gt;</code>
      </div>
      <div class="key-api-row">
        <span class="key-api-label">接口格式</span>
        <span style="font-size:13px;color:var(--text)">兼容 OpenAI Chat Completions API</span>
      </div>
      <div class="key-api-row" style="border-bottom:none">
        <span class="key-api-label">文档</span>
        <a href="https://easycode.uno/docs" target="_blank" style="font-size:13px;color:var(--primary)">easycode.uno/docs →</a>
      </div>
    </div>

    <!-- Create Token Modal -->
    <n-modal v-model:show="showCreate" :mask-closable="false" preset="card" title="创建令牌"
      style="width:620px;max-width:90vw" :bordered="true" segmented>
      <n-form label-placement="top" label-width="auto">
        <n-form-item label="令牌名称" path="name" required style="margin-bottom:0">
          <n-input v-model:value="formName" placeholder="令牌名称" />
        </n-form-item>
        <n-space style="margin-top:12px">
          <n-form-item label="分组" style="flex:1">
            <n-select v-model:value="formGroup" :options="[{ label: 'default', value: 'default' }]" />
          </n-form-item>
          <n-form-item label="到期时间" style="flex:1">
            <n-space vertical :size="4">
              <n-input v-model:value="formExpiry" placeholder="永不过期" style="min-width:120px" />
              <n-button-group size="tiny">
                <n-button :type="expiryPreset === 'forever' ? 'primary' : 'default'" @click="setExpiry('forever')">永不</n-button>
                <n-button :type="expiryPreset === '1month' ? 'primary' : 'default'" @click="setExpiry('1month')">1月</n-button>
                <n-button :type="expiryPreset === '1day' ? 'primary' : 'default'" @click="setExpiry('1day')">1天</n-button>
                <n-button :type="expiryPreset === '1hour' ? 'primary' : 'default'" @click="setExpiry('1hour')">1小时</n-button>
              </n-button-group>
            </n-space>
          </n-form-item>
          <n-form-item label="创建数量" style="width:100px">
            <n-input-number v-model:value="formCount" :min="1" :max="100" />
          </n-form-item>
        </n-space>
        <n-divider />
        <n-form-item label="额度设置" style="margin-bottom:4px">
          <n-space align="flex-end" :size="12">
            <n-form-item label="每个Key额度" style="flex:1;max-width:240px">
              <n-input-number v-model:value="formQuota" :min="0" :step="0.01" placeholder="0 = 不限制" style="width:100%" />
            </n-form-item>
            <n-checkbox v-model:checked="formUnlimited">不限额度</n-checkbox>
            <n-checkbox v-model:checked="formNativeQuota">原生额度</n-checkbox>
          </n-space>
        </n-form-item>
        <n-divider />
        <n-form-item label="访问限制">
          <n-space :size="12" style="width:100%">
            <n-form-item label="模型限制" style="flex:1">
              <n-select v-model:value="formModels" :options="modelOptions" multiple filterable placeholder="全部模型（不限）" />
            </n-form-item>
            <n-form-item label="IP 白名单" style="flex:1">
              <n-input v-model:value="formIp" placeholder="多个 IP 用逗号分隔" />
            </n-form-item>
          </n-space>
        </n-form-item>
        <n-alert v-if="newKey" type="success" :bordered="true" closable @close="newKey = ''">
          <template #header><span style="font-weight:600">令牌已生成（仅显示一次）</span></template>
          <n-space align="center" :size="8">
            <code style="flex:1;padding:8px 12px;background:#f0fdf4;border-radius:6px;font-size:12px;overflow-x:auto;white-space:nowrap;display:block">{{ newKey }}</code>
            <n-button size="small" type="primary" @click="copyText(newKey)">复制</n-button>
          </n-space>
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end" :size="10">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="createKey">{{ creating ? '创建中...' : '创建' }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- API Call Modal -->
    <n-modal v-model:show="showApiModal" preset="card" title="API 调用测试" style="max-width:720px">
      <div style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">
        基于 Chat Completions API 生成调用代码，替换 API Key 后直接调用。
      </div>
      <n-form label-placement="top">
        <n-space :size="16">
          <n-form-item label="API Key">
            <n-input :value="apiCallKeyPrefix" disabled style="width:220px">
              <template #prefix>🔑</template>
            </n-input>
          </n-form-item>
          <n-form-item label="目标模型">
            <n-select v-model:value="apiCallModel" :options="modelOptions" placeholder="-- 选择模型 --" filterable style="width:200px" />
          </n-form-item>
        </n-space>
      </n-form>
      <n-divider />
      <h5 style="margin:0 0 12px;font-size:14px;font-weight:600">代码示例</h5>
      <n-tabs type="line" :value="codeTab" @update:value="codeTab = $event">
        <n-tab-pane name="curl" tab="cURL">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(curlCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ curlCode }}</pre>
        </n-tab-pane>
        <n-tab-pane name="python" tab="Python">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(pythonCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ pythonCode }}</pre>
        </n-tab-pane>
        <n-tab-pane name="node" tab="Node.js">
          <n-button size="tiny" quaternary style="float:right" @click="copyCode(nodeCode)">复制</n-button>
          <pre style="background:var(--bg);padding:12px;border-radius:6px;font-size:11px;line-height:1.6;overflow-x:auto">{{ nodeCode }}</pre>
        </n-tab-pane>
      </n-tabs>
      <n-space :size="12" style="margin-top:12px">
        <n-button size="small" type="primary" :loading="apiCalling" :disabled="!apiCallModel" @click="doApiCall">▶ 运行测试</n-button>
      </n-space>
      <n-alert v-if="apiResult" :type="apiResultType" :bordered="true" style="font-size:12px;margin-top:12px">
        <pre style="margin:0;white-space:pre-wrap;max-height:200px;overflow-y:auto">{{ apiResult }}</pre>
      </n-alert>
      <n-alert v-if="apiError" type="error" :bordered="true" closable @close="apiError = ''" style="margin-top:8px;font-size:12px">{{ apiError }}</n-alert>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  NButton, NButtonGroup, NCheckbox, NDataTable, NDivider,
  NEmpty, NForm, NFormItem, NInput, NInputNumber, NModal, NPopconfirm,
  NSelect, NSpace, NAlert, NTabs, NTabPane,
} from 'naive-ui'
import { api } from '../api'
import { gatewayApi } from '../gatewayApi'

const message = useMessage()
const dialog = useDialog()

const keys = ref([])
const selected = ref([])
const searchName = ref('')
const searchKey = ref('')
const filterStatus = ref('')
const showCreate = ref(false)
const newKey = ref('')
const creating = ref(false)
const formName = ref('')
const formGroup = ref('default')
const formExpiry = ref('')
const formCount = ref(1)
const formQuota = ref(0)
const formUnlimited = ref(false)
const formNativeQuota = ref(false)
const formModels = ref([])
const formIp = ref('')
const expiryPreset = ref('forever')
const availableModels = ref([])
const monthCalls = ref(0)
const codeTab = ref('curl')
const showApiModal = ref(false)
const apiCallKeyPrefix = ref('')
const apiCallKeyId = ref('')
const apiCallModel = ref(null)
const apiCalling = ref(false)
const apiResult = ref('')
const apiResultType = ref('success')
const apiError = ref('')

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '有效', value: 'active' },
  { label: '已撤销', value: 'revoked' },
  { label: '已过期', value: 'expired' },
]

const modelOptions = computed(() =>
  availableModels.value.map(m => ({ label: m.id, value: m.id }))
)

const activeCount = computed(() => keys.value.filter(k => k.status === 'active').length)

const filteredKeys = computed(() => {
  let list = keys.value
  if (searchName.value) list = list.filter(k => (k.name || '').toLowerCase().includes(searchName.value.toLowerCase()))
  if (searchKey.value) list = list.filter(k => k.key_prefix.includes(searchKey.value))
  if (filterStatus.value) list = list.filter(k => k.status === filterStatus.value)
  return list
})

function statusColor(status) {
  if (status === 'active') return 'var(--status-active)'
  if (status === 'expired') return 'var(--status-expired)'
  return 'var(--status-revoked)'
}
function statusLabel(status) {
  if (status === 'active') return '有效'
  if (status === 'expired') return '已过期'
  return '已撤销'
}

const tableColumns = computed(() => [
  { type: 'selection', width: 40 },
  { title: '名称 / Key', key: 'name', minWidth: 180,
    render: row => h('div', [
      h('div', { style: 'font-weight:600;font-size:13px' }, row.name || '未命名'),
      h('code', { style: 'font-size:11px;color:var(--text-muted)' }, row.key_prefix + '••••••'),
    ])
  },
  { title: '状态', key: 'status', width: 80,
    render: row => h('span', {
      style: `display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:${statusColor(row.status)}1a;color:${statusColor(row.status)}`
    }, statusLabel(row.status))
  },
  { title: '配额', key: 'quota', width: 160,
    render: row => {
      if (row.quota_total == null || row.quota_total === 0) {
        return h('span', { style: 'font-size:12px;color:var(--text-muted)' }, '不限')
      }
      const used = row.quota_used || 0
      const total = row.quota_total
      const pct = Math.min(Math.round((used / total) * 100), 100)
      const warn = pct >= 80
      return h('div', [
        h('div', { style: 'height:4px;background:var(--border-light);border-radius:2px;margin-bottom:4px;width:100px' }, [
          h('div', { style: `height:4px;border-radius:2px;width:${pct}%;background:${warn ? 'var(--quota-warn)' : 'var(--primary)'}` })
        ]),
        h('span', { style: `font-size:11px;${warn ? 'font-weight:700;color:var(--quota-warn)' : ''}` }, `${used} / ${total}`)
      ])
    }
  },
  { title: '最后调用', key: 'last_used_at', width: 110,
    render: row => h('span', { style: 'font-size:12px' }, row.last_used_at ? fmtDate(row.last_used_at) : '从未')
  },
  { title: '到期', key: 'expires_at', width: 100,
    render: row => h('span', { style: 'font-size:12px' }, row.expires_at ? fmtDate(row.expires_at) : '永不')
  },
  { title: '操作', key: 'actions', width: 150,
    render: row => {
      if (row.status === 'active') {
        return h('div', { style: 'display:flex;gap:4px;flex-wrap:wrap' }, [
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => copyFullKey(row.id) }, { default: () => '复制' }),
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => openApiCall(row) }, { default: () => 'API测试' }),
          h(NPopconfirm, { onPositiveClick: () => revokeKey(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', style: 'color:var(--status-revoked)' }, { default: () => '撤销' }),
            default: () => '确定撤销此令牌？',
          }),
        ])
      }
      if (row.status === 'expired') {
        return h('div', { style: 'display:flex;gap:4px' }, [
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => copyFullKey(row.id) }, { default: () => '复制' }),
          h(NPopconfirm, { onPositiveClick: () => deleteKey(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', style: 'color:var(--status-revoked)' }, { default: () => '删除' }),
            default: () => '确定永久删除？',
          }),
        ])
      }
      return h(NButton, { size: 'tiny', quaternary: true, disabled: true }, { default: () => '已撤销' })
    }
  },
])

function fmtDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '-' }

const curlCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `curl -X POST https://easycode.uno/v1/chat/completions \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer ${apiCallKeyPrefix.value}" \\\n  -d '{"model":"${model}","messages":[{"role":"user","content":"你好"}]}'`
})
const pythonCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `from openai import OpenAI\nclient = OpenAI(api_key="${apiCallKeyPrefix.value}", base_url="https://easycode.uno/v1")\nresponse = client.chat.completions.create(model="${model}", messages=[{"role":"user","content":"你好"}])\nprint(response.choices[0].message.content)`
})
const nodeCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `import OpenAI from 'openai';\nconst client = new OpenAI({apiKey:"${apiCallKeyPrefix.value}",baseURL:"https://easycode.uno/v1"});\nconst r = await client.chat.completions.create({model:"${model}",messages:[{role:"user",content:"你好"}]});\nconsole.log(r.choices[0].message.content);`
})

function copyCode(code) {
  navigator.clipboard.writeText(typeof code === 'string' ? code : code.value).then(() => message.success('已复制'))
}

function openApiCall(row) {
  apiCallKeyPrefix.value = row.key_prefix + '...'
  apiCallKeyId.value = row.id
  apiCallModel.value = null
  apiResult.value = ''; apiError.value = ''
  showApiModal.value = true
}

async function doApiCall() {
  if (!apiCallModel.value) return
  apiCalling.value = true; apiResult.value = ''; apiError.value = ''
  try {
    const res = await fetch('/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': apiCallKeyId.value },
      body: JSON.stringify({ model: apiCallModel.value, messages: [{ role: 'user', content: 'hi' }], max_tokens: 100 })
    })
    const data = await res.json()
    apiResult.value = JSON.stringify(data, null, 2)
    apiResultType.value = res.ok ? 'success' : 'error'
  } catch (e) { apiError.value = e.message } finally { apiCalling.value = false }
}

onMounted(async () => {
  try { const d = await api.listKeys(); keys.value = d.items } catch (e) { console.error('listKeys failed', e) }
  try { const m = await gatewayApi.listModels(); availableModels.value = m.data || [] } catch (e) { /* */ }
  try {
    const now = new Date()
    const from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
    const to = now.toISOString().slice(0, 10)
    const u = await api.getUsage(1, from, to)
    monthCalls.value = u.total_calls || (u.items || []).length
  } catch (e) { /* */ }
})

function setExpiry(preset) {
  expiryPreset.value = preset
  const now = new Date()
  if (preset === 'forever') { formExpiry.value = ''; return }
  if (preset === '1hour') now.setHours(now.getHours() + 1)
  if (preset === '1day') now.setDate(now.getDate() + 1)
  if (preset === '1month') now.setMonth(now.getMonth() + 1)
  formExpiry.value = now.toISOString().slice(0, 16)
}

async function createKey() {
  if (!formName.value) { message.warning('请输入令牌名称'); return }
  creating.value = true
  try {
    let expireDays = null
    if (expiryPreset.value === '1hour') expireDays = 0
    else if (expiryPreset.value === '1day') expireDays = 1
    else if (expiryPreset.value === '1month') expireDays = 30
    const modelsStr = formModels.value.length > 0 ? formModels.value.join(',') : null
    const data = await api.createKey(formName.value, 60, {
      token_group: formGroup.value || 'default',
      token_quota: formUnlimited.value ? null : (formQuota.value || null),
      ip_whitelist: formIp.value || null,
      model_allowlist: modelsStr,
      expire_days: expireDays,
      count: formCount.value || 1,
    })
    newKey.value = data.api_key || (data.keys && data.keys[0]?.api_key)
    const list = await api.listKeys(); keys.value = list.items
    formName.value = ''; formExpiry.value = ''; formCount.value = 1; formQuota.value = 0; formIp.value = ''
    message.success('令牌创建成功')
  } catch (e) { message.error(e.message || '创建失败') } finally { creating.value = false }
}

async function copyFullKey(id) {
  try { const d = await api.revealKey(id); await copyText(d.api_key); message.success('已复制') }
  catch (e) { message.error('复制失败') }
}

async function revokeKey(id) {
  try {
    await api.revokeKey(id)
    const d = await api.listKeys(); keys.value = d.items
    selected.value = selected.value.filter(x => x !== id)
    message.success('已撤销')
  } catch (e) { message.error('撤销失败') }
}

async function deleteKey(id) {
  try {
    await api.deleteKey(id)
    const d = await api.listKeys(); keys.value = d.items
    selected.value = selected.value.filter(x => x !== id)
    message.success('已删除')
  } catch (e) { message.error('删除失败') }
}

async function batchRevoke() {
  const ids = [...selected.value]
  let failed = 0
  for (const id of ids) { try { await api.revokeKey(id) } catch (e) { failed++ } }
  const d = await api.listKeys(); keys.value = d.items; selected.value = []
  if (failed) message.error(`${failed} 个撤销失败`); else message.success(`已撤销 ${ids.length} 个`)
}

async function batchDelete() {
  const ids = [...selected.value]
  let failed = 0
  for (const id of ids) { try { await api.deleteKey(id) } catch (e) { failed++ } }
  const d = await api.listKeys(); keys.value = d.items; selected.value = []
  if (failed) message.error(`${failed} 个删除失败`); else message.success(`已删除 ${ids.length} 个`)
}

function doSearch() { /* filteredKeys is reactive */ }

async function copyText(text) {
  try { await navigator.clipboard.writeText(text) } catch (e) {
    const ta = document.createElement('textarea'); ta.value = text
    ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
  }
}
</script>

<style scoped>
.key-summary-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px;
}
.key-summary-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 16px 20px;
}
.ksc-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.ksc-value { font-size: 28px; font-weight: 700; color: var(--text); }
.key-toolbar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 12px 16px;
}
.key-table-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); overflow: hidden;
}
.key-table-footer {
  padding: 10px 16px; font-size: 12px; color: var(--text-muted);
  border-top: 1px solid var(--border-light);
}
.key-api-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px; margin-top: 16px;
}
.key-api-title {
  font-size: 13px; font-weight: 600; color: var(--text);
  margin-bottom: 14px; padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
}
.key-api-row {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 0; border-bottom: 1px solid var(--border-light);
}
.key-api-label {
  font-size: 12px; color: var(--text-secondary); width: 80px; flex-shrink: 0;
}
.key-api-code {
  font-family: var(--font-mono); font-size: 12px;
  background: var(--primary-light); color: var(--primary);
  padding: 2px 8px; border-radius: 4px;
}
</style>
