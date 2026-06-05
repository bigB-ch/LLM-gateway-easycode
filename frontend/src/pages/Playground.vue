<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 56px - 48px)">
    <h1 class="page-title mb-16">Playground</h1>

    <div class="card card-padded mb-16">
      <div style="display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap">
        <div style="min-width:200px">
          <label class="form-label">模型</label>
          <select v-model="selectedModel" class="form-select">
            <option value="">{{ t('selectModel') }}</option>
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.id }}</option>
          </select>
        </div>
        <div>
          <label class="form-label">Temperature: {{ temperature }}</label>
          <input type="range" v-model.number="temperature" min="0" max="2" step="0.1" style="width:120px" />
        </div>
        <div>
          <label class="form-label">Max Tokens</label>
          <input v-model.number="maxTokens" type="number" class="form-input" placeholder="默认" min="1" style="width:110px" />
        </div>
        <button class="btn btn-outline" @click="clearChat">{{ t('clear') }}</button>
      </div>
    </div>

    <div ref="chatArea" class="card card-padded" style="flex:1;overflow-y:auto;margin-bottom:12px">
      <div v-if="messages.length === 0" class="empty-state" style="padding-top:60px">
        <div class="empty-state-icon">&#x1F4AC;</div>
        <div class="empty-state-text">{{ t('playgroundHint') }}</div>
        <div class="empty-state-sub">{{ t('modelListHint') }}</div>
      </div>
      <div v-for="(msg, i) in messages" :key="i" :style="{display:'flex',justifyContent:msg.role==='user'?'flex-end':'flex-start',marginBottom:'16px'}">
        <div :class="'chat-bubble ' + msg.role">
          <div v-if="msg.role !== 'error'" style="font-size:11px;margin-bottom:4px;opacity:0.6;font-weight:500">
            {{ msg.role === 'user' ? 'You' : selectedModel }}
          </div>
          {{ msg.content }}
          <div v-if="msg.usage" class="text-muted mt-8">
            {{ msg.usage.prompt_tokens }} + {{ msg.usage.completion_tokens }} tokens
            <span v-if="msg.latency_ms"> &middot; {{ msg.latency_ms }}ms</span>
          </div>
        </div>
      </div>
      <div v-if="loading" style="margin-bottom:16px">
        <div class="chat-bubble assistant" style="color:var(--text-muted)">{{ t('thinking') }}</div>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div style="display:flex;gap:10px">
      <textarea v-model="inputMessage" @keydown.enter.exact.prevent="sendMessage"
        :placeholder="t('inputMsgHint')" :disabled="loading || !selectedModel"
        rows="3" class="form-textarea" style="flex:1"></textarea>
      <button class="btn btn-primary" @click="sendMessage"
        :disabled="loading || !selectedModel || !inputMessage.trim()"
        style="padding:12px 28px;font-size:14px;align-self:flex-end">
        {{ loading ? t('sending') : t('send') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
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
