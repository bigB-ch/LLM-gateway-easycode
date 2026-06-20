<template>
  <div class="auth-page">
<div class="auth-geo-ring"></div><div class="auth-geo-dot"></div><div class="auth-geo-bar"></div><div class="auth-geo-bar2"></div>
    <div class="auth-topbar">
      <router-link to="/" class="auth-logo"><LogoIcon :size="64" /><span class="brand-text" style="font-size:26px">Easy<span class="brand-accent">Code</span></span></router-link>
    </div>
    <div class="auth-card auth-card-lg">
      <n-h1>{{ t('registerTitle') }}</n-h1>
      <p class="subtitle gradient-text">{{ t('registerSubtitle') }}</p>
      <n-form @submit.prevent="step === 1 ? sendCode() : verifyCode()">
        <template v-if="step === 1">
          <n-form-item :label="t('username')" required>
            <n-input v-model:value="username" :placeholder="t('username')" />
          </n-form-item>
          <n-form-item label="Email" required>
            <n-input v-model:value="email" type="email" placeholder="you@example.com" />
          </n-form-item>
          <n-form-item :label="t('password')" required>
            <n-input v-model:value="password" type="password" placeholder="Min 8 chars, upper+lower+digit" show-password-on="click" />
          </n-form-item>
        </template>
        <template v-else>
          <p class="verify-tip">{{ t('codeSent') }} <strong>{{ email }}</strong></p>
          <n-form-item :label="t('verifyCode')" required>
            <n-input v-model:value="code" :placeholder="t('verifyCode')" maxlength="6" />
          </n-form-item>
        </template>
        <n-alert v-if="error" type="error" :bordered="true" closable @close="error = ''" style="margin-bottom:12px">{{ error }}</n-alert>
        <n-alert v-if="success" type="success" :bordered="true" closable @close="success = ''" style="margin-bottom:12px">{{ success }}</n-alert>
        <n-button type="primary" attr-type="submit" :loading="loading" style="width:100%;padding:12px 0;font-size:15px">
          {{ loading ? t('processing') : step === 1 ? t('sendVerifyCode') : t('verifyAndLogin') }}
        </n-button>
      </n-form>
      <p class="auth-footer">{{ t('hasAccount') }}<router-link to="/login">{{ t('goLogin') }}</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NH1, NInput, NAlert } from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
import LogoIcon from '../components/LogoIcon.vue'
import { useTheme } from '../composables/useTheme'
const { t } = useI18n()
const { isDark, toggleTheme } = useTheme()
const router = useRouter(); const step = ref(1)
const username = ref(''); const email = ref(''); const password = ref(''); const code = ref('')
const loading = ref(false); const error = ref(''); const success = ref('')
function validatePassword(pw) {
  if (pw.length < 8) return 'Password must be 8+ chars'
  if (!/[A-Z]/.test(pw)) return 'Need uppercase'
  if (!/[a-z]/.test(pw)) return 'Need lowercase'
  if (!/[0-9]/.test(pw)) return 'Need digit'
  return null
}
async function sendCode() {
  error.value = ''; success.value = ''
  const pwErr = validatePassword(password.value)
  if (pwErr) { error.value = pwErr; return }
  loading.value = true
  try {
    await api.register(username.value, email.value, password.value)
    step.value = 2; success.value = t('codeSent')
  } catch (e) { error.value = e.message === 'email_exists' ? t('emailExists') : t('registerFailed') }
  finally { loading.value = false }
}
async function verifyCode() {
  loading.value = true; error.value = ''
  try {
    const data = await api.verifyCode(email.value, code.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.user.role)
    router.push(data.user.role === 'admin' || data.user.role === 'super_admin' ? '/admin' : '/')
  } catch (e) { error.value = t('codeError') }
  finally { loading.value = false }
}
</script>
