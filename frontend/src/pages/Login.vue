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
      <h1>登录</h1>
      <p class="subtitle gradient-text">让 Coding 更简单</p>
      <form @submit.prevent="login">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input v-model="username" type="text" class="form-input" placeholder="输入用户名" required />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input v-model="password" type="password" class="form-input" placeholder="输入密码" required />
        </div>
        <div v-if="error" class="alert alert-error" style="display:flex;justify-content:space-between;align-items:center">
          <span>{{ error }}</span>
          <button class="alert-close" @click="error = ''">&times;</button>
        </div>
        <button type="submit" class="btn btn-primary btn-login" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
      <p class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
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
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function login() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.login(username.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.user.role)
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
</script>
