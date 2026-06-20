<template>
  <div>
    <div class="flex-between mb-16">
      <h1 class="page-title">{{ t('tokenManagement') }}</h1>
      <n-button size="small" @click="compactView = !compactView">
        {{ compactView ? t('defaultView') : t('compactList') }}
      </n-button>
    </div>

    <!-- Batch action bar -->
    <n-card :bordered="true" style="margin-bottom:16px;padding:12px 16px">
      <n-space align="center" wrap :size="[10, 8]">
        <n-button type="primary" size="small" @click="showCreate = true">
          {{ t('addToken') }}
        </n-button>
        <n-button size="small" :disabled="!selected.length" @click="batchCopy">
          {{ t('copySelected') }}
        </n-button>
        <n-popconfirm @positive-click="batchRevoke" @positive="batchRevoke">
          <template #trigger>
            <n-button size="small" color="#dc2626" :disabled="!selected.length">
              吊销所选
            </n-button>
          </template>
          确定吊销 {{ selected.length }} 个令牌？吊销后不可恢复。
        </n-popconfirm>
        <n-popconfirm @positive-click="batchDelete" @positive="batchDelete">
          <template #trigger>
            <n-button size="small" color="#dc2626" :disabled="!selected.length">
              删除所选
            </n-button>
          </template>
          确定永久删除 {{ selected.length }} 个令牌？此操作不可恢复！
        </n-popconfirm>

        <div style="flex:1" />

        <n-input
          v-model:value="searchName"
          :placeholder="t('keySearch')"
          clearable
          style="width:160px"
          size="small"
          @keyup.enter="doSearch"
        />
        <n-input
          v-model:value="searchKey"
          :placeholder="t('keySearch')"
          clearable
          style="width:180px"
          size="small"
          @keyup.enter="doSearch"
        />
        <n-button type="primary" size="small" @click="doSearch">{{ t('query') }}</n-button>
        <n-button size="small" @click="resetSearch">{{ t('reset') }}</n-button>
      </n-space>
    </n-card>

    <!-- Create Token Modal -->
    <n-modal v-model:show="showCreate" :mask-closable="false" preset="card" title="创建令牌"
      style="width:620px;max-width:90vw" :bordered="true" segmented>
      <n-form label-placement="top" label-width="auto">
        <!-- Section 1: Basic Info -->
        <n-form-item :label="t('tokenName')" path="name" required style="margin-bottom:0">
          <n-input v-model:value="formName" :placeholder="t('tokenName')" />
        </n-form-item>
        <n-space style="margin-top:12px">
          <n-form-item :label="t('tokenGroup')" style="flex:1">
            <n-select v-model:value="formGroup" :options="[{ label: 'default', value: 'default' }]" />
          </n-form-item>
          <n-form-item :label="t('expiryTime')" style="flex:1">
            <n-space vertical :size="4">
              <n-input v-model:value="formExpiry" placeholder="永不过期" style="min-width:120px" />
              <n-button-group size="tiny">
                <n-button :type="expiryPreset === 'forever' ? 'primary' : 'default'" @click="setExpiry('forever')">{{ t('never') }}</n-button>
                <n-button :type="expiryPreset === '1month' ? 'primary' : 'default'" @click="setExpiry('1month')">{{ t('oneMonth') }}</n-button>
                <n-button :type="expiryPreset === '1day' ? 'primary' : 'default'" @click="setExpiry('1day')">{{ t('oneDay') }}</n-button>
                <n-button :type="expiryPreset === '1hour' ? 'primary' : 'default'" @click="setExpiry('1hour')">{{ t('oneHour') }}</n-button>
              </n-button-group>
            </n-space>
          </n-form-item>
          <n-form-item :label="t('createCount')" style="width:100px">
            <n-input-number v-model:value="formCount" :min="1" :max="100" />
          </n-form-item>
        </n-space>

        <!-- Section 2: Quota -->
        <n-divider />
        <n-form-item label="&#x1F4B0; 额度设置" style="margin-bottom:4px">
          <n-space align="flex-end" :size="12">
            <n-form-item :label="t('tokenQuotaPer')" style="flex:1;max-width:240px">
              <n-input-number v-model:value="formQuota" :min="0" :step="0.01" placeholder="0 = 不限制" style="width:100%" />
            </n-form-item>
            <n-checkbox v-model:checked="formUnlimited">{{ t('unlimitedQuota') }}</n-checkbox>
            <n-checkbox v-model:checked="formNativeQuota">{{ t('nativeQuota') }}</n-checkbox>
          </n-space>
        </n-form-item>

        <!-- Section 3: Access Control -->
        <n-divider />
        <n-form-item label="&#x1F512; 访问限制">
          <n-space :size="12" style="width:100%">
            <n-form-item :label="t('modelRestrict')" style="flex:1">
              <n-select v-model:value="formModels" :options="modelOptions" multiple filterable placeholder="全部模型（不限）" />
            </n-form-item>
            <n-form-item :label="t('ipRestrict')" style="flex:1">
              <n-input v-model:value="formIp" :placeholder="t('ipHint')" />
            </n-form-item>
          </n-space>
        </n-form-item>

        <!-- Generated key result -->
        <n-alert v-if="newKey" type="success" :bordered="true" closable @close="newKey = ''">
          <template #header>
            <span style="font-weight:600">{{ t('tokenGenerated') }}</span>
          </template>
          <n-space align="center" :size="8">
            <code style="flex:1;padding:8px 12px;background:#f0fdf4;border-radius:6px;font-size:12px;overflow-x:auto;white-space:nowrap;display:block">{{ newKey }}</code>
            <n-button size="small" type="primary" @click="copyText(newKey)">复制完整密钥</n-button>
          </n-space>
        </n-alert>
      </n-form>

      <template #footer>
        <n-space justify="end" :size="10">
          <n-button @click="showCreate = false">{{ t('cancel') }}</n-button>
          <n-button type="primary" :loading="creating" @click="createKey">{{ creating ? '创建中...' : t('submit') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- API Call Modal -->
    <n-modal v-model:show="showApiModal" preset="card" title="API 调用测试" style="max-width:720px">
      <div style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">
        基于 Chat Completions API（兼容 OpenAI 对话标准接口）生成调用代码，替换 API Key 后直接调用服务。
      </div>
      <n-form label-placement="top">
        <n-space :size="16">
          <n-form-item label="API Key">
            <n-input :value="apiCallKeyPrefix" disabled style="width:220px">
              <template #prefix>&#x1F511;</template>
            </n-input>
          </n-form-item>
          <n-form-item label="目标模型">
            <n-select v-model:value="apiCallModel" :options="modelOptions" placeholder="-- 选择模型 --" filterable style="width:200px" />
          </n-form-item>
        </n-space>
      </n-form>
      <n-divider />
      <h5 style="margin:0 0 12px 0;font-size:14px;font-weight:600">&#x1F4DD; 代码示例</h5>
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
        <n-button size="small" type="primary" :loading="apiCalling" :disabled="!apiCallModel" @click="doApiCall">&#x25B6; 运行测试</n-button>
      </n-space>
      <n-alert v-if="apiResult" :type="apiResultType" :bordered="true" style="font-size:12px;margin-top:12px">
        <pre style="margin:0;white-space:pre-wrap;max-height:200px;overflow-y:auto">{{ apiResult }}</pre>
      </n-alert>
      <n-alert v-if="apiError" type="error" :bordered="true" closable @close="apiError = ''" style="margin-top:8px;font-size:12px">{{ apiError }}</n-alert>

      <n-divider />
      <n-collapse>
        <n-collapse-item title="&#x1F527; AI 工具接入配置参考">
          <n-tabs type="line" size="small">
            <n-tab-pane name="claude" tab="Claude Code">
              <div style="font-size:12px;line-height:1.8">
                <p><b>安装：</b><code style="font-size:11px">npm install -g @anthropic-ai/claude-code</code></p>
                <p><b>环境变量：</b></p>
                <pre style="background:var(--bg);padding:10px;border-radius:6px;font-size:11px">export ANTHROPIC_API_KEY={{ apiCallKeyPrefix }}
export ANTHROPIC_BASE_URL=https://easycode.uno</pre>
                <p><b>授权：</b><code style="font-size:11px">cc auth login --provider anthropic</code></p>
                <p><b>使用：</b><code style="font-size:11px">cc "你的问题"</code></p>
              </div>
            </n-tab-pane>
            <n-tab-pane name="openclaw" tab="OpenClaw">
              <div style="font-size:12px;line-height:1.8">
                <p><b>安装：</b><code style="font-size:11px">npm install -g openclaw</code></p>
                <p><b>配置：</b></p>
                <pre style="background:var(--bg);padding:10px;border-radius:6px;font-size:11px">openclaw config set ANTHROPIC_API_KEY {{ apiCallKeyPrefix }}
openclaw config set ANTHROPIC_BASE_URL https://easycode.uno</pre>
                <p><b>使用：</b><code style="font-size:11px">openclaw "你的问题"</code></p>
              </div>
            </n-tab-pane>
            <n-tab-pane name="codex" tab="OpenAI SDK">
              <div style="font-size:12px;line-height:1.8">
                <p><b>Python：</b><code style="font-size:11px">pip install openai</code></p>
                <pre style="background:var(--bg);padding:10px;border-radius:6px;font-size:11px">from openai import OpenAI
client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://easycode.uno/v1"
)
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "hello"}]
)</pre>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-collapse-item>
      </n-collapse>
    </n-modal>

    <!-- Data table -->
    <n-card :bordered="true">
      <n-data-table
        v-if="filteredKeys.length"
        :columns="tableColumns"
        :data="filteredKeys"
        :row-key="(row) => row.id"
        :checked-row-keys="selected"
        :single-line="false"
        :size="compactView ? 'small' : 'medium'"
        :min-height="200"
        @update:checked-row-keys="selected = $event"
      />
      <n-empty v-else description="暂无数据" style="padding:40px 0">
        <template #extra>
          <n-button size="small" @click="showCreate = true">{{ t('addToken') }}</n-button>
        </template>
      </n-empty>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import {
  NButton, NButtonGroup, NCard, NCheckbox, NDataTable, NDivider,
  NEmpty, NForm, NFormItem, NInput, NInputNumber, NModal, NPopconfirm,
  NSelect, NSpace, NTag, NAlert, NTabs, NTabPane,
} from 'naive-ui'
import { api } from '../api'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

const keys = ref([])
const showCreate = ref(false)
const newKeyName = ref('')
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
const compactView = ref(false)
const codeTab = ref('curl')

const curlCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `curl -X POST https://easycode.uno/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${apiCallKeyPrefix.value}" \
  -d '{
    "model": "${model}",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'`
})

const pythonCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `from openai import OpenAI

client = OpenAI(
    api_key="${apiCallKeyPrefix.value}",
    base_url="https://easycode.uno/v1"
)

response = client.chat.completions.create(
    model="${model}",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)`
})

const nodeCode = computed(() => {
  const model = apiCallModel.value || 'deepseek-v4-flash'
  return `import OpenAI from 'openai';

const client = new OpenAI({
    apiKey: "${apiCallKeyPrefix.value}",
    baseURL: "https://easycode.uno/v1"
});

async function main() {
    const response = await client.chat.completions.create({
        model: "${model}",
        messages: [{ role: "user", content: "你好" }]
    });
    console.log(response.choices[0].message.content);
}
main();`
})

function copyCode(code) {
  navigator.clipboard.writeText(code.value || code).then(() => {
    message.success('已复制到剪贴板')
  }).catch(() => {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = code.value || code
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    message.success('已复制到剪贴板')
  })
}

const showApiModal = ref(false)
const apiCallKeyPrefix = ref('')
const apiCallKeyId = ref('')
const apiCallModel = ref(null)
const apiCalling = ref(false)
const apiResult = ref('')
const apiResultType = ref('success')
const apiError = ref('')

function openApiCall(row) {
  apiCallKeyPrefix.value = row.key_prefix + '...'
  apiCallKeyId.value = row.id
  apiCallModel.value = null
  apiResult.value = ''
  apiError.value = ''
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
  } catch(e) { apiError.value = e.message } finally { apiCalling.value = false }
}

const selected = ref([])
const searchName = ref('')
const searchKey = ref('')

const modelOptions = computed(() =>
  availableModels.value.map(m => ({ label: m.id, value: m.id }))
)

const filteredKeys = computed(() => {
  let list = keys.value
  if (searchName.value) {
    const q = searchName.value.toLowerCase()
    list = list.filter(k => (k.name || '').toLowerCase().includes(q))
  }
  if (searchKey.value) {
    list = list.filter(k => k.key_prefix.includes(searchKey.value))
  }
  return list
})

const allSelected = computed(() =>
  filteredKeys.value.length > 0 && filteredKeys.value.every(k => selected.value.includes(k.id))
)

const tableColumns = computed(() => [
  { type: 'selection', width: 40 },
  { title: '名称', key: 'name', width: 100,
    render: (row) => row.name || '未命名' },
  { title: t('status'), key: 'status', width: 70,
    render: (row) => h(NTag, {
      type: row.status === 'active' ? 'success' : 'default',
      size: 'small',
    }, { default: () => row.status === 'active' ? t('active') : t('revoked') }) },
  { title: '剩余额度 / 总额度', key: 'quota', width: 140,
    render: (row) => {
      if (row.quota_used != null) {
        return `${row.quota_used} / ${row.quota_total || '∞'}`
      }
      return '-'
    } },
  { title: t('groups'), key: 'group', width: 80,
    render: (row) => row.group || '默认' },
  { title: t('key'), key: 'key_prefix', minWidth: 160,
    render: (row) => h('div', { style: 'display:flex;align-items:center;gap:6px' }, [
      h('code', { style: 'font-family:var(--font-mono);font-size:12px;color:var(--text)' },
        row.key_prefix + '•••'),
      row.status === 'active'
        ? h(NButton, { size: 'tiny', quaternary: true, onClick: () => copyFullKey(row.id) },
            { default: () => t('copy') })
        : null,
    ]) },
  { title: t('availableModels'), key: 'models', width: 120,
    render: (row) => row.models || '全部' },
  { title: t('ipRestrict'), key: 'ip_whitelist', width: 90,
    render: (row) => row.ip_whitelist || '不限' },
  { title: t('createTime'), key: 'created_at', width: 110,
    render: (row) => fmtDate(row.created_at) },
  { title: t('lastUsed'), key: 'last_used_at', width: 130,
    render: (row) => row.last_used_at ? fmtDate(row.last_used_at) : '从未使用' },
  { title: t('expiryTime'), key: 'expires_at', width: 100,
    render: (row) => row.expires_at ? fmtDate(row.expires_at) : '永不过期' },
  { title: t('operation'), key: 'actions', width: 130,
    render: (row) => {
      if (row.status === 'active') {
        return h('div', { style: 'display:flex;gap:4px;flex-wrap:wrap' }, [
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => openApiCall(row) },
            { default: () => 'API 调用' }),
          h(NButton, { size: 'tiny', quaternary: true, onClick: () => regenerateKey(row) },
            { default: () => '重新生成' }),
          h(NPopconfirm, {
            onPositiveClick: () => revokeKey(row.id),
          }, {
            trigger: () => h(NButton, { size: 'tiny', color: '#dc2626' },
              { default: () => '吊销' }),
            default: () => '确定吊销此令牌？吊销后不可恢复。',
          }),
        ])
      }
      return h(NPopconfirm, {
        onPositiveClick: () => deleteKey(row.id),
      }, {
        trigger: () => h(NButton, { size: 'tiny', color: '#dc2626' },
          { default: () => '删除' }),
        default: () => '确定永久删除此令牌？此操作不可恢复！',
      })
    } },
])

function fmtDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const data = await api.listKeys()
    keys.value = data.items
  } catch (e) { /* */ }
  try {
    const models = await gatewayApi.listModels()
    availableModels.value = models.data || []
  } catch (e) { /* */ }
})

function setExpiry(preset) {
  expiryPreset.value = preset
  const now = new Date()
  if (preset === '1hour') now.setHours(now.getHours() + 1)
  if (preset === '1day') now.setDate(now.getDate() + 1)
  if (preset === '1month') now.setMonth(now.getMonth() + 1)
  if (preset === 'forever') { formExpiry.value = ''; return }
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

    const modelsStr = formModels.value.length > 0
      ? formModels.value.filter(m => m !== '').join(',') : null

    const data = await api.createKey(formName.value || null, 60, {
      token_group: formGroup.value || 'default',
      token_quota: formUnlimited.value ? null : (formQuota.value || null),
      ip_whitelist: formIp.value || null,
      model_allowlist: modelsStr,
      expire_days: expireDays,
      count: formCount.value || 1,
    })
    newKey.value = data.api_key || (data.keys && data.keys[0]?.api_key)
    const list = await api.listKeys()
    keys.value = list.items
    formName.value = ''
    formExpiry.value = ''
    formCount.value = 1
    formQuota.value = 0
    formIp.value = ''
    message.success('令牌创建成功')
  } catch (e) {
    message.error(e.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function copyFullKey(id) {
  try {
    const data = await api.revealKey(id)
    await copyText(data.api_key)
    message.success('已复制')
  } catch (e) {
    message.error('复制失败: ' + (e.message || '未知错误'))
  }
}

async function revokeKey(id) {
  try {
    await api.revokeKey(id)
    const data = await api.listKeys()
    keys.value = data.items
    selected.value = selected.value.filter(x => x !== id)
    message.success('已吊销')
  } catch (e) {
    message.error('吊销失败: ' + (e.message || '未知错误'))
  }
}

async function deleteKey(id) {
  try {
    await api.deleteKey(id)
    const data = await api.listKeys()
    keys.value = data.items
    selected.value = selected.value.filter(x => x !== id)
    message.success('已删除')
  } catch (e) {
    message.error('删除失败: ' + (e.message || '未知错误'))
  }
}

async function regenerateKey(key) {
  dialog.warning({
    title: '重新生成令牌',
    content: '重新生成将吊销旧令牌并创建新令牌，旧令牌立即失效。确定继续？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const data = await api.createKey(key.name || 'regenerated', key.rate_limit || 60, {
          token_group: key.token_group || 'default',
          ip_whitelist: key.ip_whitelist || null,
          model_allowlist: key.models || null,
          count: 1,
        })
        await api.revokeKey(key.id)
        newKey.value = data.api_key || (data.keys && data.keys[0]?.api_key)
        showCreate.value = true
        const list = await api.listKeys()
        keys.value = list.items
        message.success('已重新生成')
      } catch (e) {
        message.error('重新生成失败: ' + (e.message || '未知错误'))
      }
    },
  })
}

async function batchRevoke() {
  if (!selected.value.length) return
  let failed = 0
  for (const id of selected.value) {
    try { await api.revokeKey(id) } catch (e) { failed++ }
  }
  if (failed) message.error(`${failed} 个吊销失败`)
  const data = await api.listKeys()
  keys.value = data.items
  selected.value = []
  message.success(`已吊销 ${selected.value.length} 个令牌`)
}

async function batchDelete() {
  if (!selected.value.length) return
  let failed = 0
  for (const id of selected.value) {
    try { await api.deleteKey(id) } catch (e) { failed++ }
  }
  if (failed) message.error(`${failed} 个删除失败`)
  const data = await api.listKeys()
  keys.value = data.items
  selected.value = []
  message.success(`已删除 ${selected.value.length} 个令牌`)
}

function batchCopy() {
  const texts = keys.value.filter(k => selected.value.includes(k.id)).map(k => k.key_prefix).join('\n')
  copyText(texts || ' ')
  message.success('已复制')
}

function doSearch() { /* filteredKeys is reactive */ }
function resetSearch() { searchName.value = ''; searchKey.value = '' }

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
}
</script>
