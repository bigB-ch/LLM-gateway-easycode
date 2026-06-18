<template>
  <div>
    <!-- Banner -->
    <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:28px 32px;border-radius:var(--radius-lg);display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:20px">
      <n-space :size="16" align="center">
        <div style="width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,0.2);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px">{{ avatarChar }}</div>
        <div>
          <n-text style="font-size:18px;font-weight:700;color:#fff;display:block">{{ userName }}</n-text>
          <n-space :size="10" style="margin-top:4px">
            <n-text style="font-size:12px;color:rgba(255,255,255,0.7)">{{ t('userRole') }}</n-text>
            <n-text style="font-size:12px;color:rgba(255,255,255,0.5)">{{ t('userIdLabel') }}: {{ userId }}</n-text>
            <n-tag size="tiny" style="background:rgba(255,255,255,0.15);color:#fca5a5">余额 &yen;{{ balance }}</n-tag>
          </n-space>
        </div>
      </n-space>
      <n-space :size="32">
        <div><n-text style="font-size:10px;text-transform:uppercase;color:rgba(255,255,255,0.5);display:block">{{ t('totalSpent') }}</n-text><n-text style="font-size:18px;font-weight:700;color:#fff">&yen;{{ totalCost }}</n-text></div>
        <div><n-text style="font-size:10px;text-transform:uppercase;color:rgba(255,255,255,0.5);display:block">{{ t('requests') }}</n-text><n-text style="font-size:18px;font-weight:700;color:#fff">{{ totalCalls }}</n-text></div>
        <div><n-text style="font-size:10px;text-transform:uppercase;color:rgba(255,255,255,0.5);display:block">{{ t('userGroup') }}</n-text><n-text style="font-size:18px;font-weight:700;color:#fff">default</n-text></div>
      </n-space>
    </div>

    <n-grid :x-gap="16" :y-gap="16" :cols="2">
      <!-- Card 1: Account -->
      <n-grid-item>
        <n-card :bordered="true">
          <template #header>
            <n-tabs v-model:value="acctTab" size="small" :tabs-padding="0" style="margin:0">
              <n-tab name="bind">{{ t('accountBind') }}</n-tab>
              <n-tab name="security">{{ t('securitySettings') }}</n-tab>
            </n-tabs>
          </template>

          <div v-if="acctTab === 'bind'">
            <n-h3 style="margin:0 0 16px">{{ t('multiChannelBind') }}</n-h3>
            <n-space vertical :size="4">
              <div class="flex-between" style="padding:10px 12px;border-radius:var(--radius-sm);border:1px solid transparent;cursor:default">
                <n-space :size="12" align="center">
                  <n-text style="font-size:20px;width:32px;text-align:center">&#x2709;</n-text>
                  <div><n-text style="font-size:13px;font-weight:500">{{ t('email') }}</n-text><n-text depth="3" style="font-size:11px;display:block;margin-top:1px">{{ userEmail }} <n-text style="color:var(--success)">{{ t('emailBound') }}</n-text></n-text></div>
                </n-space>
                <n-text depth="3" style="font-size:12px">{{ t('supportModify') }}</n-text>
              </div>
              <div v-for="b in bindItems" :key="b.name" class="flex-between" style="padding:10px 12px;border-radius:var(--radius-sm);cursor:default">
                <n-space :size="12" align="center">
                  <n-text style="font-size:20px;width:32px;text-align:center">{{ b.icon }}</n-text>
                  <div><n-text style="font-size:13px;font-weight:500">{{ b.name }}</n-text><n-text depth="3" style="font-size:11px;display:block;margin-top:1px">{{ b.status }}</n-text></div>
                </n-space>
                <n-button size="tiny" v-if="b.action">{{ b.action }}</n-button>
              </div>
            </n-space>
          </div>

          <div v-else>
            <n-h3 style="margin:0 0 16px">{{ t('changePassword') }}</n-h3>
            <n-form label-placement="top" label-width="auto">
              <n-form-item :label="t('oldPassword')" style="max-width:320px">
                <n-input v-model:value="oldPw" type="password" :placeholder="t('oldPassword')" />
              </n-form-item>
              <n-form-item :label="t('newPwd')" style="max-width:320px">
                <n-input v-model:value="newPw" type="password" :placeholder="t('newPwd')" />
              </n-form-item>
              <n-form-item :label="t('confirmPwd')" style="max-width:320px">
                <n-input v-model:value="confirmPw" type="password" :placeholder="t('confirmPwd')" />
              </n-form-item>
              <n-alert v-if="pwError" type="error" :bordered="true" closable @close="pwError = ''">{{ pwError }}</n-alert>
              <n-alert v-if="pwSuccess" type="success" :bordered="true" closable @close="pwSuccess = ''">{{ pwSuccess }}</n-alert>
              <n-button type="primary" size="small" :loading="pwLoading" @click="changePw" style="margin-top:8px">{{ pwLoading ? t('saving') : t('save') }}</n-button>
            </n-form>
          </div>
        </n-card>
      </n-grid-item>

      <!-- Card 2: Notifications -->
      <n-grid-item>
        <n-card :bordered="true">
          <template #header>
            <n-tabs v-model:value="otherTab" size="small" :tabs-padding="0" style="margin:0">
              <n-tab name="notify">{{ t('notifications') }}</n-tab>
              <n-tab name="price">{{ t('priceDisplay') }}</n-tab>
              <n-tab name="about">{{ t('about') }}</n-tab>
            </n-tabs>
          </template>

          <div v-if="otherTab === 'notify'">
            <n-h3 style="margin:0 0 16px">{{ t('notifyConfig') }}</n-h3>
            <n-form-item :label="t('notifyMethod')">
              <n-radio-group v-model:value="notifyMethod">
                <n-radio value="email">{{ t('emailNotify') }}</n-radio>
                <n-radio value="webhook">{{ t('webhookNotify') }}</n-radio>
                <n-radio value="bark">{{ t('barkNotify') }}</n-radio>
                <n-radio value="gotify">{{ t('gotifyNotify') }}</n-radio>
              </n-radio-group>
            </n-form-item>
            <n-form-item :label="t('alertThreshold')">
              <n-space :size="8" align="center">
                <n-text>等价 ¥</n-text>
                <n-input-number v-model:value="alertThreshold" style="width:120px" />
                <n-text depth="3">余额低于阈值时触发提醒</n-text>
              </n-space>
            </n-form-item>
            <n-form-item :label="t('notifyEmail')">
              <n-input :placeholder="t('notifyEmailHint')" style="max-width:280px" />
            </n-form-item>
            <n-alert v-if="settingsMsg" :type="settingsMsg.includes(t('settingsSaved')) ? 'success' : 'error'" :bordered="true">{{ settingsMsg }}</n-alert>
            <n-button type="primary" size="small" :loading="savingSettings" @click="saveSettings" style="margin-top:8px">{{ savingSettings ? t('saving') : t('saveSettings') }}</n-button>
          </div>
          <div v-else-if="otherTab === 'price'">
            <n-empty :description="t('inDevelopment')" style="padding:24px" />
          </div>
          <div v-else>
            <n-space vertical :size="6">
              <n-text depth="2" style="font-size:13px;line-height:2">{{ t('platformVersion') }}：{{ platformVersion }}</n-text>
              <n-text depth="2" style="font-size:13px;line-height:2">{{ t('registeredAt') }}：{{ registeredAt }}</n-text>
              <n-text depth="2" style="font-size:13px;line-height:2">{{ t('lastLoginAt') }}：{{ lastLoginAt }}</n-text>
            </n-space>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-text depth="3" style="text-align:center;display:block;padding:16px 0;font-size:12px">&copy;2026 EasyCode {{ t('allRightsReserved') || '版权所有' }}</n-text>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NButton, NEmpty, NForm, NFormItem, NGrid, NGridItem, NH3,
  NInput, NInputNumber, NRadio, NRadioGroup, NSpace, NTab, NTabs,
  NTag, NText, NAlert,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const userName = ref(''); const userEmail = ref(''); const userId = ref('')
const balance = ref('0.00'); const totalCost = ref('0.00'); const totalCalls = ref(0)
const acctTab = ref('bind'); const otherTab = ref('notify')
const notifyMethod = ref('email'); const alertThreshold = ref(500000)
const oldPw = ref(''); const newPw = ref(''); const confirmPw = ref('')
const pwError = ref(''); const pwSuccess = ref(''); const pwLoading = ref(false)
const platformVersion = ref('v1.0.0'); const registeredAt = ref('-'); const lastLoginAt = ref('-')
const savingSettings = ref(false); const settingsMsg = ref('')
const avatarChar = computed(() => userName.value ? userName.value.charAt(0).toUpperCase() : '?')

const bindItems = [
  { icon: '🐙', name: 'GitHub', status: t('githubNotBound'), action: t('bind') },
  { icon: '🧑', name: 'LinuxDO', status: t('linuxdoNotBound'), action: t('bind') },
  { icon: '📱', name: t('wechatNotEnabled'), status: t('wechatNotEnabled'), action: null },
  { icon: '🎮', name: 'Discord', status: t('discordNotEnabled'), action: null },
]

async function changePw() {
  pwError.value = ''; pwSuccess.value = ''
  if (!oldPw.value || !newPw.value || !confirmPw.value) { pwError.value = t('pwFieldsRequired'); return }
  if (newPw.value !== confirmPw.value) { pwError.value = t('pwMismatch'); return }
  if (newPw.value.length < 8) { pwError.value = t('pwTooShort'); return }
  if (!/[A-Z]/.test(newPw.value)) { pwError.value = t('pwNeedUpper'); return }
  if (!/[a-z]/.test(newPw.value)) { pwError.value = t('pwNeedLower'); return }
  if (!/[0-9]/.test(newPw.value)) { pwError.value = t('pwNeedDigit'); return }
  pwLoading.value = true
  try {
    await api.changePassword(oldPw.value, newPw.value)
    pwSuccess.value = t('passwordChanged'); oldPw.value = ''; newPw.value = ''; confirmPw.value = ''
  } catch (e) { pwError.value = e.message || t('pwChangeFailed') } finally { pwLoading.value = false }
}

async function saveSettings() {
  savingSettings.value = true; settingsMsg.value = ''
  try {
    await api.saveSettings({ notifyMethod: notifyMethod.value, alertThreshold: alertThreshold.value })
    settingsMsg.value = t('settingsSaved'); setTimeout(() => { settingsMsg.value = '' }, 3000)
  } catch (e) { settingsMsg.value = t('saveSettingsFailed') + ': ' + (e.message || '') } finally { savingSettings.value = false }
}

onMounted(async () => {
  try {
    const user = await api.getMe()
    userName.value = user.username || ''; userEmail.value = user.email || ''
    userId.value = user.id ? user.id.slice(0, 8) : '-'
    balance.value = ((user.balance || 0) / 100).toFixed(2)
    registeredAt.value = user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-'
    lastLoginAt.value = user.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-CN') : '-'
  } catch (e) { /* */ }
  try { const d = await api.getDashboard(); totalCalls.value = d.today_calls || 0; totalCost.value = d.today_cost_yuan || '0.00' } catch (e) { /* */ }
  try { const s = await api.getSettings(); if (s.settings?.notifyMethod) notifyMethod.value = s.settings.notifyMethod; if (s.settings?.alertThreshold) alertThreshold.value = s.settings.alertThreshold } catch (e) { /* */ }
})
</script>
