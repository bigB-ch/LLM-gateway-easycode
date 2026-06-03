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
    <div class="auth-card auth-card-lg">
      <h1>注册</h1>
      <p class="subtitle gradient-text">迈出 Coding 第一步</p>
      <form @submit.prevent="step === 1 ? sendCode() : verifyCode()">
        <template v-if="step === 1">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input v-model="username" type="text" class="form-input" placeholder="你的用户名" required />
          </div>
          <div class="form-group">
            <label class="form-label">邮箱</label>
            <input v-model="email" type="email" class="form-input" placeholder="you@example.com" required />
            <p class="form-hint">验证码将发送到此邮箱</p>
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <input v-model="password" type="password" class="form-input" placeholder="至少 8 位，包含大小写字母和数字" required />
            <p class="form-hint">至少 8 位，需包含大写字母、小写字母和数字</p>
          </div>
        </template>
        <template v-else>
          <p class="verify-tip">验证码已发送到 <strong>{{ email }}</strong>，请查收邮件</p>
          <div class="form-group">
            <label class="form-label">验证码</label>
            <input v-model="code" type="text" class="form-input" placeholder="输入 6 位验证码" maxlength="6" required />
          </div>
        </template>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>
        <button type="submit" class="btn btn-primary btn-login" :disabled="loading">
          {{ loading ? '处理中...' : step === 1 ? '发送邮箱验证码' : '验证并登录' }}
        </button>
      </form>
      <p class="auth-footer">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import LogoIcon from '../components/LogoIcon.vue'

const isDark = ref(document.documentElement.classList.contains('dark'))
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const router = useRouter()
const step = ref(1)
const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

function validatePassword(pw) {
  if (pw.length < 8) return '密码至少 8 位'
  if (!/[A-Z]/.test(pw)) return '密码需包含大写字母'
  if (!/[a-z]/.test(pw)) return '密码需包含小写字母'
  if (!/[0-9]/.test(pw)) return '密码需包含数字'
  return null
}

async function sendCode() {
  error.value = ''
  success.value = ''

  const pwErr = validatePassword(password.value)
  if (pwErr) { error.value = pwErr; return }

  loading.value = true
  try {
    await api.register(username.value, email.value, password.value)
    step.value = 2
    success.value = '验证码已发送，请查收邮件（开发模式下验证码打印在 Admin 终端）'
  } catch (e) {
    error.value = e.message === 'email_exists' ? '该邮箱已注册' : '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function verifyCode() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.verifyCode(email.value, code.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.user.role)
    if (data.user.role === 'admin' || data.user.role === 'super_admin') {
      router.push('/admin')
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = '验证码错误或已过期'
  } finally {
    loading.value = false
  }
}
</script>
