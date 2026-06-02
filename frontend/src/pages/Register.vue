<template>
  <div style="max-width:400px;margin:100px auto;padding:32px;">
    <h2>注册</h2>
    <form @submit.prevent="step === 1 ? sendCode() : verifyCode()">
      <div v-if="step === 1">
        <div><input v-model="username" placeholder="用户名" required style="width:100%;padding:8px;margin:8px 0" /></div>
        <div><input v-model="email" type="email" placeholder="邮箱" required style="width:100%;padding:8px;margin:8px 0" /></div>
        <div><input v-model="password" type="password" placeholder="密码" required style="width:100%;padding:8px;margin:8px 0" /></div>
      </div>
      <div v-else>
        <p>验证码已发送到 {{ email }}</p>
        <div><input v-model="code" placeholder="6位验证码" required style="width:100%;padding:8px;margin:8px 0" maxlength="6" /></div>
      </div>
      <div v-if="error" style="color:red;margin:8px 0">{{ error }}</div>
      <div v-if="success" style="color:green;margin:8px 0">{{ success }}</div>
      <button type="submit" :disabled="loading" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">
        {{ loading ? '处理中...' : step === 1 ? '发送验证码' : '验证并登录' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const step = ref(1)
const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

async function sendCode() {
  loading.value = true
  error.value = ''
  try {
    await api.register(username.value, email.value, password.value)
    step.value = 2
    success.value = '验证码已发送，请查收邮件'
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
    router.push('/admin')
  } catch (e) {
    error.value = '验证码错误或已过期'
  } finally {
    loading.value = false
  }
}
</script>
