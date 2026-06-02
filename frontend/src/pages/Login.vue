<template>
  <div style="max-width:400px;margin:100px auto;padding:32px;">
    <h2>登录 LLM Gateway</h2>
    <form @submit.prevent="login">
      <div><input v-model="email" type="email" placeholder="邮箱" required style="width:100%;padding:8px;margin:8px 0" /></div>
      <div><input v-model="password" type="password" placeholder="密码" required style="width:100%;padding:8px;margin:8px 0" /></div>
      <div v-if="error" style="color:red;margin:8px 0">{{ error }}</div>
      <button type="submit" :disabled="loading" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
    <p style="margin-top:16px;text-align:center">
      还没有账号？<router-link to="/admin/register">注册</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function login() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.login(email.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    router.push('/admin')
  } catch (e) {
    error.value = '邮箱或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
