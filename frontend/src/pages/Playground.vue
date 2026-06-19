<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 56px - 48px);width:100%">

    <!-- Top: Model selector bar -->
    <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border-light);margin-bottom:12px">
      <div style="font-size:18px;font-weight:600;white-space:nowrap">Playground</div>
      <n-select v-model:value="selectedModel" :options="modelOptions" :placeholder="'-- 选择模型 --'" style="width:200px" size="small" />
      <div style="display:flex;align-items:center;gap:4px;font-size:12px;color:var(--text-muted)">
        Temp <n-slider v-model:value="temperature" :min="0" :max="2" :step="0.1" style="width:80px" />
        <span style="min-width:24px">{{ temperature }}</span>
      </div>
      <n-input-number v-model:value="maxTokens" :min="1" placeholder="Max" style="width:90px" size="small" />
      <n-button size="tiny" quaternary @click="clearChat" style="color:var(--text-muted);margin-left:auto">清空</n-button>
    </div>

    <!-- Middle: Chat area -->
    <div ref="chatArea" style="flex:1;overflow-y:auto;padding:8px 0;margin-bottom:12px">
      <n-empty v-if="messages.length === 0" :description="t('playgroundHint')" style="padding-top:80px">
        <template #extra>
          <n-text depth="3" style="font-size:12px;display:block;margin-top:8px">{{ t('modelListHint') }}</n-text>
        </template>
      </n-empty>
      <div v-for="(msg, i) in messages" :key="i" :style="{display:'flex',justifyContent:msg.role==='user'?'flex-end':'flex-start',marginBottom:'16px'}">
        <div style="max-width:75%;padding:12px 16px;border-radius:12px;background:msg.role==='user'?'var(--primary)':'var(--surface)';color:msg.role==='user'?'#fff':'var(--text)';border:1px solid var(--border-light);line-height:1.6;white-space:pre-wrap;word-break:break-word;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
          <div v-if="msg.role !== 'error'" style="font-size:11px;margin-bottom:4px;opacity:0.6;font-weight:500">
            {{ msg.role === 'user' ? 'You' : (selectedModel || 'Assistant') }}
          </div>
          {{ msg.content }}
          <div v-if="msg.usage" style="margin-top:8px;font-size:11px;opacity:0.6">
            {{ msg.usage.prompt_tokens }} + {{ msg.usage.completion_tokens }} tokens
            <span v-if="msg.latency_ms"> &middot; {{ msg.latency_ms }}ms</span>
          </div>
        </div>
      </div>
      <div v-if="loading" style="margin-bottom:16px;display:flex;justify-content:flex-start">
        <div style="padding:12px 16px;border-radius:12px;background:var(--surface);border:1px solid var(--border-light);color:var(--text-muted);max-width:75%">{{ t('thinking') }}</div>
      </div>
    </div>

    <n-alert v-if="error" type="error" :bordered="true" closable @close="error = ''" style="margin-bottom:8px;font-size:12px">{{ error }}</n-alert>

    <!-- Bottom: Input area -->
    <div style="display:flex;gap:10px;align-items:flex-end;margin-bottom:16px">
      <n-input v-model:value="inputMessage" type="textarea" rows="2" :placeholder="selectedModel ? t('inputMsgHint') : '请先选择模型'" :disabled="loading || !selectedModel" style="flex:1;min-height:44px;font-size:14px" @keydown.enter.exact.prevent="sendMessage" />
      <n-button type="primary" :loading="loading" :disabled="loading || !selectedModel || !inputMessage.trim()" @click="sendMessage" style="height:44px;padding:0 24px;font-size:14px;border-radius:8px">
        {{ loading ? t('sending') : t('send') }}
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  NButton, NEmpty, NInput, NInputNumber, NSelect, NSlider, NText, NAlert,
} from 'naive-ui'
import { gatewayApi } from '../gatewayApi'
import { useI18n } from '../i18n'
const { t } = useI18n()

const models = ref([])
const selectedModel = ref('')
const temperature = ref(0.7)
const maxTokens = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const error = ref('')
const chatArea = ref(null)

const modelOptions = computed(() =>
  models.value.map(m => ({ label: m.id, value: m.id }))
)

onMounted(async () => {
  try { models.value = (await gatewayApi.listModels()).data || [] } catch (e) { /* */ }
})

async function sendMessage() {
  const content = inputMessage.value.trim()
  if (!content || loading.value) return
  error.value = ''
  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  loading.value = true
  await nextTick(); scrollToBottom()
  try {
    const res = await gatewayApi.chat(selectedModel.value,
      messages.value.filter(m => m.role !== 'error').map(m => ({ role: m.role, content: m.content })),
      temperature.value, maxTokens.value ? Number(maxTokens.value) : null)
    if (res.choices?.[0]) {
      const c = res.choices[0]
      messages.value.push({ role: 'assistant', content: c.message?.content || c.delta?.content || '(无回复)', usage: res.usage, latency_ms: res.latency_ms })
    }
  } catch (e) {
    messages.value.push({ role: 'error', content: '请求失败: ' + e.message })
  } finally {
    loading.value = false
    await nextTick(); scrollToBottom()
  }
}

function clearChat() { messages.value = []; error.value = '' }
function scrollToBottom() {
  if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
}
</script>
