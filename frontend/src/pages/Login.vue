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
      <button class="topbar-icon-btn" :title="isDark ? '浅色模式' : '暗色模式'" @click="toggleTheme" style="font-size:20px">
        {{ isDark ? '&#x263E;' : '&#x2600;' }}
      </button>
    </div>

    <!-- Login form -->
    <div v-if="!showReset" class="auth-card auth-card-lg">
      <h1>{{ t('loginTitle') }}</h1>
      <p class="subtitle gradient-text">{{ t('loginSubtitle') }}</p>
      <form @submit.prevent="login">
        <div class="form-group">
          <label class="form-label">{{ t('username') }}</label>
          <input v-model="username" type="text" class="form-input" :placeholder="t('username')" required />
        </div>
        <div class="form-group">
          <label class="form-label">{{ t('password') }}</label>
          <input v-model="password" type="password" class="form-input" :placeholder="t('password')" required />
        </div>
        <div class="flex-between" style="margin-bottom:12px">
          <label class="form-label" style="margin:0;display:flex;align-items:center;gap:6px;cursor:pointer">
            <input type="checkbox" v-model="rememberMe" style="accent-color:var(--primary)" />
            <span style="font-size:12px">{{ t('rememberMe') }}</span>
          </label>
          <a class="forgot-link" @click.prevent="showReset = true">{{ t('forgotPassword') }}</a>
        </div>
        <div v-if="error" class="alert alert-error" style="display:flex;justify-content:space-between;align-items:center">
          <span>{{ error }}</span>
          <button class="alert-close" @click="error = ''">&times;</button>
        </div>
        <button type="submit" class="btn btn-primary btn-login" :disabled="loading">
          {{ loading ? t('loggingIn') : t('loginBtn') }}
        </button>
      </form>
      <p class="auth-footer">
        {{ t('noAccount') }}<router-link to="/register">{{ t('registerNow') }}</router-link>
      </p>
    </div>

    <!-- Reset password form -->
    <div v-else class="auth-card auth-card-lg">
      <h1>{{ t('resetPwdTitle') }}</h1>
      <p class="subtitle gradient-text">{{ t('resetPwdSubtitle') }}</p>

      <!-- Step 1: enter email -->
      <div v-if="resetStep === 1">
        <div class="form-group">
          <label class="form-label">{{ t('regEmail') }}</label>
          <input v-model="resetEmail" type="email" class="form-input" :placeholder="t('regEmail')" required />
        </div>
        <div v-if="resetError" class="alert alert-error" style="display:flex;justify-content:space-between;align-items:center">
          <span>{{ resetError }}</span>
          <button class="alert-close" @click="resetError = ''">&times;</button>
        </div>
        <div v-if="resetMsg" class="alert" style="background:rgba(16,185,129,0.12);color:var(--success);border:1px solid rgba(16,185,129,0.25);display:flex;justify-content:space-between;align-items:center">
          <span>{{ resetMsg }}</span>
          <button class="alert-close" @click="resetMsg = ''">&times;</button>
        </div>
        <button class="btn btn-primary btn-login" :disabled="sendingCode" @click="sendResetCode">
          {{ sendingCode ? t('sendingCode') : t('sendCode') }}
        </button>
      </div>

      <!-- Step 2: enter code + new password -->
      <div v-else>
        <div class="form-group">
          <label class="form-label">{{ t('verifyCode') }}</label>
          <input v-model="resetCode" type="text" class="form-input" placeholder="6-digit code" maxlength="6" required />
        </div>
        <div class="form-group">
          <label class="form-label">{{ t('newPassword') }}</label>
          <input v-model="resetNewPw" type="password" class="form-input" placeholder="Min 8 chars, upper+lower+digit" required />
        </div>
        <div class="form-group">
          <label class="form-label">{{ t('confirmPassword') }}</label>
          <input v-model="resetNewPw2" type="password" class="form-input" placeholder="Re-enter new password" required />
        </div>
        <div v-if="resetError" class="alert alert-error" style="display:flex;justify-content:space-between;align-items:center">
          <span>{{ resetError }}</span>
          <button class="alert-close" @click="resetError = ''">&times;</button>
        </div>
        <button class="btn btn-primary btn-login" :disabled="resetting" @click="doResetPassword">
          {{ resetting ? t('resetting') : t('resetPwdBtn') }}
        </button>
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

// Restore remembered email
const saved = localStorage.getItem('remembered_login')
if (saved) { username.value = saved; rememberMe.value = true }

// ── Login ──
async function login() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.login(username.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.user.role)
    if (rememberMe.value) {
      localStorage.setItem('remembered_login', username.value)
    } else {
      localStorage.removeItem('remembered_login')
    }
    if (data.user.role === 'admin' || data.user.role === 'super_admin') {
      router.push('/admin')
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = e.message === 'invalid_credentials' ? '用户名或密码错误' : (e.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// ── Forgot Password ──
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
  sendingCode.value = true
  resetError.value = ''
  resetMsg.value = ''
  try {
    await api.forgotPassword(resetEmail.value)
    resetMsg.value = '验证码已发送，请检查邮箱（开发模式下查看控制台输出）'
    resetStep.value = 2
  } catch (e) {
    resetError.value = e.message === 'email_not_found' ? '该邮箱未注册' : e.message === 'too_many_codes' ? '发送过于频繁，请稍后再试' : (e.message || '发送失败')
  } finally {
    sendingCode.value = false
  }
}

async function doResetPassword() {
  resetError.value = ''
  if (!resetCode.value || resetCode.value.length !== 6) {
    resetError.value = '请输入6位验证码'
    return
  }
  if (resetNewPw.value.length < 8) {
    resetError.value = '密码至少8位'
    return
  }
  if (resetNewPw.value !== resetNewPw2.value) {
    resetError.value = '两次输入的密码不一致'
    return
  }
  resetting.value = true
  try {
    await api.resetPassword(resetEmail.value, resetCode.value, resetNewPw.value)
    resetMsg.value = '密码重置成功！请返回登录'
    resetStep.value = 1
    resetCode.value = ''
    resetNewPw.value = ''
    resetNewPw2.value = ''
  } catch (e) {
    resetError.value = e.message === 'invalid_or_expired_code' ? '验证码无效或已过期' : (e.message || '重置失败')
  } finally {
    resetting.value = false
  }
}

function resetAll() {
  showReset.value = false
  resetStep.value = 1
  resetError.value = ''
  resetMsg.value = ''
}
</script>

<style scoped>
.forgot-link {
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  cursor: pointer;
}
.forgot-link:hover {
  color: var(--primary);
}
</style>
