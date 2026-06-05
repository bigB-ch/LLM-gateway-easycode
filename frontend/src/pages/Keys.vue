<template>
  <div>
    <!-- Page header + actions -->
    <div class="flex-between mb-16">
      <h1 class="page-title">{{ t('tokenManagement') }}</h1>
      <button class="btn btn-outline btn-sm" @click="compactView = !compactView">
        {{ compactView ? t('defaultView') : t('compactList') }}
      </button>
    </div>

    <!-- Batch action bar -->
    <div class="card card-padded mb-16" style="padding:12px 16px">
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
        <button class="btn btn-primary btn-sm" @click="showCreate = true; dragX = 0; dragY = 0">{{ t('addToken') }}</button>
        <button class="btn btn-outline btn-sm" :disabled="!selected.length" @click="batchCopy">&#x2398; {{ t('copySelected') }}</button>
        <button class="btn btn-sm" :disabled="!selected.length" style="background:#fef2f2;color:#dc2626;border:1px solid #fecaca" @click="batchRevoke">&#x1F5D1; {{ t('deleteSelected') }}</button>

        <div style="flex:1"></div>

        <!-- Search -->
        <input v-model="searchName" class="form-input" :placeholder="t('keySearch')" style="width:160px;padding:5px 10px;font-size:13px" @keyup.enter="doSearch" />
        <input v-model="searchKey" class="form-input" :placeholder="t('keySearch')" style="width:180px;padding:5px 10px;font-size:13px" @keyup.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">{{ t('query') }}</button>
        <button class="btn btn-outline btn-sm" @click="resetSearch">{{ t('reset') }}</button>
      </div>
    </div>

    <!-- ── Create Token Modal ── -->
    <div v-if="showCreate" class="token-panel" :style="{marginLeft: dragX + 'px', marginTop: dragY + 'px'}">
      <div class="token-modal-header" @mousedown="startDrag" style="cursor:grab">
          <h2>{{ t('createToken') }}</h2>
          <button class="alert-close" @click="showCreate = false">&times;</button>
        </div>

        <div class="token-modal-body">
          <!-- Section 1: 基本信息 (blue) -->
          <div class="token-section">
            <div class="token-section-title" style="background:var(--primary-light);color:var(--primary)">
              &#x1F4CB; {{ t('basicInfo') }}
            </div>
            <div class="form-group">
              <label class="form-label">{{ t('tokenName') }} <span style="color:var(--danger)">*</span></label>
              <input v-model="formName" class="form-input" :placeholder="t('tokenName')" />
            </div>
            <div style="display:flex;gap:12px">
              <div class="form-group" style="flex:1">
                <label class="form-label">{{ t('tokenGroup') }}</label>
                <select v-model="formGroup" class="form-select">
                  <option value="default">default</option>
                </select>
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">{{ t('expiryTime') }}</label>
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
                  <input v-model="formExpiry" type="text" class="form-input" placeholder="永不过期" style="flex:1;min-width:120px" />
                </div>
                <div style="display:flex;gap:4px;margin-top:6px">
                  <button :class="'btn btn-xs ' + (expiryPreset === 'forever' ? 'btn-primary' : 'btn-outline')" @click="setExpiry('forever')">{{ t('never') }}</button>
                  <button :class="'btn btn-xs ' + (expiryPreset === '1month' ? 'btn-primary' : 'btn-outline')" @click="setExpiry('1month')">{{ t('oneMonth') }}</button>
                  <button :class="'btn btn-xs ' + (expiryPreset === '1day' ? 'btn-primary' : 'btn-outline')" @click="setExpiry('1day')">{{ t('oneDay') }}</button>
                  <button :class="'btn btn-xs ' + (expiryPreset === '1hour' ? 'btn-primary' : 'btn-outline')" @click="setExpiry('1hour')">{{ t('oneHour') }}</button>
                </div>
              </div>
              <div class="form-group" style="width:100px">
                <label class="form-label">{{ t('createCount') }}</label>
                <input v-model.number="formCount" type="number" min="1" max="100" class="form-input" />
              </div>
            </div>
          </div>

          <!-- Section 2: 额度设置 (green) -->
          <div class="token-section">
            <div class="token-section-title" style="background:#ecfdf5;color:#059669">
              &#x1F4B0; {{ t('quotaSettings') }}
            </div>
            <div style="display:flex;gap:12px;align-items:flex-end">
              <div class="form-group" style="flex:1;max-width:240px">
                <label class="form-label">{{ t('tokenQuotaPer') }}</label>
                <input v-model.number="formQuota" type="number" min="0" step="0.01" class="form-input" placeholder="0 = 不限制" />
              </div>
              <label class="filter-option" style="margin-bottom:10px">
                <input type="checkbox" v-model="formUnlimited" />
                <span>{{ t('unlimitedQuota') }}</span>
              </label>
              <label class="filter-option" style="margin-bottom:10px">
                <input type="checkbox" v-model="formNativeQuota" />
                <span>{{ t('nativeQuota') }}</span>
              </label>
            </div>
            <p class="form-hint">{{ t('quotaHint') }}</p>
          </div>

          <!-- Section 3: 访问限制 (purple) -->
          <div class="token-section">
            <div class="token-section-title" style="background:#f5f0ff;color:#7c3aed">
              &#x1F512; {{ t('accessControl') }}
            </div>
            <div style="display:flex;gap:12px">
              <div class="form-group" style="flex:1">
                <label class="form-label">{{ t('modelRestrict') }}</label>
                <select v-model="formModels" class="form-select" multiple style="min-height:100px">
                  <option value="">全部模型（不限）</option>
                  <option v-for="m in availableModels" :key="m.id" :value="m.id">{{ m.id }}</option>
                </select>
                <p class="form-hint">留空 = 全部模型开放。Ctrl/Cmd + 点击多选</p>
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">{{ t('ipRestrict') }}</label>
                <input v-model="formIp" class="form-input" :placeholder="t('ipHint')" />
              </div>
            </div>
          </div>

          <!-- Result -->
          <div v-if="newKey" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:var(--radius);padding:14px 16px;margin-top:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-weight:600;color:#166534;font-size:13px">{{ t('tokenGenerated') }}</span>
            </div>
            <div style="display:flex;gap:8px">
              <code style="flex:1;background:#fff;border:1px solid #bbf7d0;padding:10px 14px;border-radius:6px;font-family:var(--font-mono);font-size:12px;word-break:break-all">{{ newKey }}</code>
              <button class="btn btn-outline btn-sm" @click="copyText(newKey)">复制</button>
            </div>
          </div>
        </div>

        <div class="token-modal-footer">
          <button class="btn btn-primary" @click="createKey" :disabled="creating">{{ creating ? '创建中...' : '提交' }}</button>
          <button class="btn btn-outline" @click="showCreate = false">取消</button>
        </div>
    </div>

    <!-- Table -->
    <div class="card" v-if="filteredKeys.length">
      <div class="table-wrap" style="border:none;overflow-x:auto">
        <table class="data-table" :style="{fontSize: compactView ? '12px' : '14px'}">
          <thead>
            <tr>
              <th style="width:40px"><input type="checkbox" @change="toggleAll" :checked="allSelected" /></th>
              <th style="min-width:100px">名称</th>
              <th style="width:70px">状态</th>
              <th style="width:120px">剩余额度 / 总额度</th>
              <th style="width:80px">分组</th>
              <th style="min-width:160px">密钥</th>
              <th style="width:120px">可用模型</th>
              <th style="width:90px">IP 限制</th>
              <th style="width:110px">创建时间</th>
              <th style="width:130px">最后使用</th>
              <th style="width:100px">过期时间</th>
              <th style="width:60px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in filteredKeys" :key="key.id">
              <td><input type="checkbox" :value="key.id" v-model="selected" /></td>
              <td><span style="font-weight:500">{{ key.name || '未命名' }}</span></td>
              <td>
                <span :class="'badge ' + (key.status === 'active' ? 'badge-success' : 'badge-default')">
                  {{ key.status === 'active' ? t('active') : t('revoked') }}
                </span>
              </td>
              <td class="text-secondary">
                <span v-if="key.quota_used != null">{{ key.quota_used }} / {{ key.quota_total || '&infin;' }}</span>
                <span v-else>-</span>
              </td>
              <td class="text-secondary">{{ key.group || '默认' }}</td>
              <td>
                <div style="display:flex;align-items:center;gap:6px">
                  <code style="font-family:var(--font-mono);font-size:12px;color:var(--text)">{{ key.key_prefix }}&bull;&bull;&bull;</code>
                  <button class="btn btn-outline btn-xs" @click="copyText(key.key_prefix)" title="复制">&#x2398;</button>
                </div>
              </td>
              <td class="text-secondary" style="font-size:12px">{{ key.models || '全部' }}</td>
              <td class="text-secondary" style="font-size:12px">{{ key.ip_whitelist || '不限' }}</td>
              <td class="text-secondary" style="font-size:12px">{{ fmtDate(key.created_at) }}</td>
              <td class="text-secondary" style="font-size:12px">{{ key.last_used_at ? fmtDate(key.last_used_at) : '从未使用' }}</td>
              <td class="text-secondary" style="font-size:12px">{{ key.expires_at ? fmtDate(key.expires_at) : '永不过期' }}</td>
              <td>
                <button v-if="key.status === 'active'" class="btn btn-xs" style="background:#fef2f2;color:#dc2626;border:1px solid #fecaca" @click="revokeKey(key.id)">吊销</button>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="card card-padded">
      <div class="empty-state">
        <div class="empty-state-icon">&#x1F50D;</div>
        <div class="empty-state-text">{{ searchName || searchKey ? '搜索无结果' : '暂无令牌' }}</div>
        <div class="empty-state-sub">{{ searchName || searchKey ? '尝试其他搜索条件' : '点击上方按钮创建您的第一个 API 令牌' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()

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

// Drag state
const dragX = ref(0)
const dragY = ref(0)
let dragging = false, startX = 0, startY = 0

function startDrag(e) {
  dragging = true
  startX = e.clientX - dragX.value
  startY = e.clientY - dragY.value
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e) {
  if (!dragging) return
  dragX.value = e.clientX - startX
  dragY.value = e.clientY - startY
}

function stopDrag() {
  dragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}
const compactView = ref(false)
const selected = ref([])
const searchName = ref('')
const searchKey = ref('')

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

function fmtDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

function toggleAll(e) {
  if (e.target.checked) {
    selected.value = filteredKeys.value.map(k => k.id)
  } else {
    selected.value = []
  }
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
  if (!formName.value) { alert('请输入令牌名称'); return }
  creating.value = true
  try {
    let expireDays = null
    if (expiryPreset.value === '1hour') expireDays = 0
    else if (expiryPreset.value === '1day') expireDays = 1
    else if (expiryPreset.value === '1month') expireDays = 30

    const modelsStr = formModels.value.length > 0 && formModels.value[0] !== ''
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
  } catch (e) { alert(e.message) } finally { creating.value = false }
}

async function revokeKey(id) {
  if (!confirm('确定吊销此令牌？')) return
  await api.revokeKey(id)
  const data = await api.listKeys()
  keys.value = data.items
  selected.value = selected.value.filter(x => x !== id)
}

async function batchRevoke() {
  if (!selected.value.length) return
  if (!confirm(`确定吊销 ${selected.value.length} 个令牌？`)) return
  for (const id of selected.value) {
    await api.revokeKey(id).catch(() => {})
  }
  const data = await api.listKeys()
  keys.value = data.items
  selected.value = []
}

function batchCopy() {
  const texts = keys.value.filter(k => selected.value.includes(k.id)).map(k => k.key_prefix).join('\n')
  copyText(texts || ' ')
}

function doSearch() { /* filteredKeys is reactive */ }
function resetSearch() { searchName.value = ''; searchKey.value = '' }

async function copyText(text) {
  try { await navigator.clipboard.writeText(text) } catch (e) { /* */ }
}
</script>

<style scoped>
.token-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 200;
  background: var(--surface);
  border-radius: var(--radius-xl);
  width: 600px;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  border: 1px solid var(--border);
}

.token-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.token-modal-header h2 { font-size: 18px; font-weight: 700; }

.token-modal-body {
  padding: 20px 28px;
  overflow-y: auto;
  flex: 1;
}

.token-modal-footer {
  padding: 16px 28px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.token-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}
.token-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

.token-section-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 14px;
}
</style>
