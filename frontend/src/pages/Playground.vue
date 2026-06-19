<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 56px - 48px)">
    <n-h1 style="margin-bottom:16px">Playground</n-h1>

    <n-card :bordered="true" size="small" style="margin-bottom:16px">
      <n-space align="flex-end" wrap :size="16">
        <n-form-item label="模型" style="min-width:200px">
          <n-select v-model:value="selectedModel" :options="modelOptions" :placeholder="t('selectModel')" />
        </n-form-item>
        <n-form-item :label="'Temperature: ' + temperature">
          <n-slider v-model:value="temperature" :min="0" :max="2" :step="0.1" style="width:120px" />
        </n-form-item>
        <n-form-item label="Max Tokens">
          <n-input-number v-model:value="maxTokens" :min="1" placeholder="默认" style="width:110px" />
        </n-form-item>
        <n-button @click="clearChat">{{ t('clear') }}</n-button>
      </n-space>
    </n-card>

    <div ref="chatArea" class="card card-padded" style="flex:1;overflow-y:auto;margin-bottom:12px">
      <n-empty v-if="messages.length === 0" :description="t('playgroundHint')" style="padding-top:60px">
        <template #extra>
          <n-text depth="3" style="font-size:12px">{{ t('modelListHint') }}</n-text>
        </template>
      </n-empty>
      <div v-for="(msg, i) in messages" :key="i" :style="{display:'flex',justifyContent:msg.role==='user'?'flex-end':'flex-start',marginBottom:'16px'}">
        <div style="max-width:75%;padding:12px 16px;border-radius:var(--radius);background:msg.role==='user'?'var(--primary)':'var(--surface)';color:msg.role==='user'?'#fff':'var(--text)';border:1px solid var(--border-light);line-height:1.6;white-space:pre-wrap;word-break:break-word">
          <div v-if="msg.role !== 'error'" style="font-size:11px;margin-bottom:4px;opacity:0.6;font-weight:500">
            {{ msg.role === 'user' ? 'You' : selectedModel }}
          </div>
          {{ msg.content }}
          <div v-if="msg.usage" style="margin-top:8px;font-size:11px;opacity:0.6">
            {{ msg.usage.prompt_tokens }} + {{ msg.usage.completion_tokens }} tokens
            <span v-if="msg.latency_ms"> &middot; {{ msg.latency_ms }}ms</span>
          </div>
        </div>
      </div>
      <div v-if="loading" style="margin-bottom:16px">
        <div style="padding:12px 16px;border-radius:var(--radius);background:var(--surface);border:1px solid var(--border-light);color:var(--text-muted);max-width:75%">{{ t('thinking') }}</div>
      </div>
    </div>

    <n-alert v-if="error" type="error" :bordered="true" closable @close="error = ''">{{ error }}</n-alert>

    <n-space :size="10">
      <n-input v-model:value="inputMessage" type="textarea" rows="1" :placeholder="selectedModel ? t('inputMsgHint') : '请先选择模型'" :disabled="loading || !selectedModel" style="flex:1;min-height:44px" @keydown.enter.exact.prevent="sendMessage" />
      <n-button type="primary" :loading="loading" :disabled="loading || !selectedModel || !inputMessage.trim()" @click="sendMessage" style="padding:12px 28px;font-size:14px;align-self:flex-end">
        {{ loading ? t('sending') : t('send') }}
      </n-button>
    </n-space>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  NCard, NButton, NEmpty, NFormItem, NH1, NInput, NInputNumber,
  NSelect, NSlider, NSpace, NText, NAlert,
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
