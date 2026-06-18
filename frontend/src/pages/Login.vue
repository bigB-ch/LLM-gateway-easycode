<template>
  <div class="auth-page">
    <div class="auth-geo-ring"></div>
    <div class="auth-geo-dot"></div>
    <div class="auth-geo-bar"></div>
    <div class="auth-geo-bar2"></div>
    <div class="auth-topbar">
      <router-link to="/" class="auth-logo">
        <LogoIcon :size="48" />
        <span class="brand-text">Easy<span class="brand-accent">Code</span></span>
      </router-link>
      <n-button text :title="isDark ? '浅色模式' : '暗色模式'" @click="toggleTheme" style="font-size:20px;color:var(--text-muted)">
        {{ isDark ? '&#x263E;' : '&#x2600;' }}
      </n-button>
    </div>

    <!-- Login form -->
    <div v-if="!showReset" class="auth-card auth-card-lg">
      <n-h1>{{ t('loginTitle') }}</n-h1>
      <p class="subtitle gradient-text">{{ t('loginSubtitle') }}</p>
      <n-form @submit.prevent="login">
        <n-form-item :label="t('username')" required>
          <n-input v-model:value="username" :placeholder="t('username')" />
        </n-form-item>
        <n-form-item :label="t('password')" required>
          <n-input v-model:value="password" type="password" :placeholder="t('password')" show-password-on="click" />
        </n-form-item>
        <div class="flex-between" style="margin-bottom:12px">
          <n-checkbox v-model:checked="rememberMe" style="font-size:12px">{{ t('rememberMe') }}</n-checkbox>
          <a class="forgot-link" @click.prevent="showReset = true">{{ t('forgotPassword') }}</a>
        </div>
        <n-alert v-if="error" type="error" :bordered="true" closable @close="error = ''" style="margin-bottom:12px">
          {{ error }}
        </n-alert>
        <n-button type="primary" attr-type="submit" :loading="loading" style="width:100%;padding:12px 0;font-size:15px">
          {{ loading ? t('loggingIn') : t('loginBtn') }}
        </n-button>
      </n-form>
      <p class="auth-footer">
        {{ t('noAccount') }}<router-link to="/register">{{ t('registerNow') }}</router-link>
      </p>
    </div>

    <!-- Reset password form -->
    <div v-else class="auth-card auth-card-lg">
      <n-h1>{{ t('resetPwdTitle') }}</n-h1>
      <p class="subtitle gradient-text">{{ t('resetPwdSubtitle') }}</p>

      <div v-if="resetStep === 1">
        <n-form-item :label="t('regEmail')" required>
          <n-input v-model:value="resetEmail" type="email" :placeholder="t('regEmail')" />
        </n-form-item>
        <n-alert v-if="resetError" type="error" :bordered="true" closable @close="resetError = ''" style="margin-bottom:12px">{{ resetError }}</n-alert>
        <n-alert v-if="resetMsg" type="success" :bordered="true" closable @close="resetMsg = ''" style="margin-bottom:12px">{{ resetMsg }}</n-alert>
        <n-button type="primary" :loading="sendingCode" @click="sendResetCode" style="width:100%">
          {{ sendingCode ? t('sendingCode') : t('sendCode') }}
        </n-button>
      </div>

      <div v-else>
        <n-form-item :label="t('verifyCode')" required>
          <n-input v-model:value="resetCode" :placeholder="t('verifyCode')" maxlength="6" />
        </n-form-item>
        <n-form-item :label="t('newPassword')" required>
          <n-input v-model:value="resetNewPw" type="password" :placeholder="t('newPassword')" show-password-on="click" />
        </n-form-item>
        <n-form-item :label="t('confirmPassword')" required>
          <n-input v-model:value="resetNewPw2" type="password" :placeholder="t('confirmPassword')" show-password-on="click" />
        </n-form-item>
        <n-alert v-if="resetError" type="error" :bordered="true" closable @close="resetError = ''" style="margin-bottom:12px">{{ resetError }}</n-alert>
        <n-button type="primary" :loading="resetting" @click="doResetPassword" style="width:100%">
          {{ resetting ? t('resetting') : t('resetPwdBtn') }}
        </n-button>
      </div>

      <p class="auth-footer">
        <a @click.prevent="resetAll" style="cursor:pointer">{{ t('backToLogin') }}</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NCheckbox, NForm, NFormItem, NH1, NInput, NAlert,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
import LogoIcon from '../components/LogoIcon.vue'
import { useTheme } from '../composables/useTheme'

const { t } = useI18n()
const { isDark, toggleTheme } = useTheme()

const router = useRouter()
const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

const saved = localStorage.getItem('remembered_login')
if (saved) { username.value = saved; rememberMe.value = true }

async function login() {
  loading.value = true; error.value = ''
  try {
    const data = await api.login(username.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.user.role)
    if (rememberMe.value) localStorage.setItem('remembered_login', username.value)
    else localStorage.removeItem('remembered_login')
    router.push(data.user.role === 'admin' || data.user.role === 'super_admin' ? '/admin' : '/')
  } catch (e) {
    error.value = e.message === 'invalid_credentials' ? '用户名或密码错误' : (e.message || '登录失败')
  } finally { loading.value = false }
}

const showReset = ref(false)
const resetStep = ref(1)
const resetEmail = ref('')
const resetCode = ref('')
const resetNewPw = ref('')
const resetNewPw2 = ref('')
const sendingCode = ref(false)
const resetting = ref(false)
const resetError = ref('')
const resetMsg = ref('')

async function sendResetCode() {
  if (!resetEmail.value) return
  sendingCode.value = true; resetError.value = ''; resetMsg.value = ''
  try {
    await api.forgotPassword(resetEmail.value)
    resetMsg.value = '验证码已发送，请检查邮箱'
    resetStep.value = 2
  } catch (e) {
    resetError.value = e.message === 'email_not_found' ? '该邮箱未注册' : e.message === 'too_many_codes' ? '发送过于频繁，请稍后再试' : (e.message || '发送失败')
  } finally { sendingCode.value = false }
}

async function doResetPassword() {
  resetError.value = ''
  if (!resetCode.value || resetCode.value.length !== 6) { resetError.value = '请输入6位验证码'; return }
  if (resetNewPw.value.length < 8) { resetError.value = '密码至少8位'; return }
  if (resetNewPw.value !== resetNewPw2.value) { resetError.value = '两次输入的密码不一致'; return }
  resetting.value = true
  try {
    await api.resetPassword(resetEmail.value, resetCode.value, resetNewPw.value)
    resetMsg.value = '密码重置成功！请返回登录'
    resetStep.value = 1; resetCode.value = ''; resetNewPw.value = ''; resetNewPw2.value = ''
  } catch (e) {
    resetError.value = e.message === 'invalid_or_expired_code' ? '验证码无效或已过期' : (e.message || '重置失败')
  } finally { resetting.value = false }
}

function resetAll() { showReset.value = false; resetStep.value = 1; resetError.value = ''; resetMsg.value = '' }
</script>

<style scoped>
.forgot-link { font-size:12px;color:var(--text-secondary);text-decoration:none;cursor:pointer; }
.forgot-link:hover { color:var(--primary); }
</style>
