<template>
  <div class="auth-page">
    <div class="auth-geo-ring"></div><div class="auth-geo-dot"></div><div class="auth-geo-bar"></div><div class="auth-geo-bar2"></div>
    <div class="auth-topbar">
      <router-link to="/" class="auth-logo"><LogoIcon :size="48" /><span class="brand-text">Easy<span class="brand-accent">Code</span></span></router-link>
      <button class="topbar-icon-btn" :title="isDark ? 'Light' : 'Dark'" @click="toggleTheme" style="font-size:20px">{{ isDark ? '&#x263E;' : '&#x2600;' }}</button>
    </div>
    <div class="auth-card auth-card-lg">
      <h1>{{ t('registerTitle') }}</h1>
      <p class="subtitle gradient-text">{{ t('registerSubtitle') }}</p>
      <form @submit.prevent="step === 1 ? sendCode() : verifyCode()">
        <template v-if="step === 1">
          <div class="form-group"><label class="form-label">{{ t('username') }}</label><input v-model="username" type="text" class="form-input" :placeholder="t('username')" required /></div>
          <div class="form-group"><label class="form-label">Email</label><input v-model="email" type="email" class="form-input" placeholder="you@example.com" required /><p class="form-hint">{{ t('codeSent') }}</p></div>
          <div class="form-group"><label class="form-label">{{ t('password') }}</label><input v-model="password" type="password" class="form-input" placeholder="Min 8 chars, upper+lower+digit" required /><p class="form-hint">Min 8 chars, upper+lower+digit</p></div>
        </template>
        <template v-else>
          <p class="verify-tip">{{ t('codeSent') }} <strong>{{ email }}</strong></p>
          <div class="form-group"><label class="form-label">{{ t('verifyCode') }}</label><input v-model="code" type="text" class="form-input" placeholder="6-digit code" maxlength="6" required /></div>
        </template>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>
        <button type="submit" class="btn btn-primary btn-login" :disabled="loading">{{ loading ? t('processing') : step === 1 ? t('sendVerifyCode') : t('verifyAndLogin') }}</button>
      </form>
      <p class="auth-footer">{{ t('hasAccount') }}<router-link to="/login">{{ t('goLogin') }}</router-link></p>
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
const router = useRouter(); const step = ref(1)
const username = ref(''); const email = ref(''); const password = ref(''); const code = ref('')
const loading = ref(false); const error = ref(''); const success = ref('')
function validatePassword(pw) { if(pw.length<8) return 'Password must be 8+ chars'; if(!/[A-Z]/.test(pw)) return 'Need uppercase'; if(!/[a-z]/.test(pw)) return 'Need lowercase'; if(!/[0-9]/.test(pw)) return 'Need digit'; return null }
async function sendCode() { error.value=''; success.value=''; const pwErr=validatePassword(password.value); if(pwErr){error.value=pwErr;return}; loading.value=true; try{await api.register(username.value,email.value,password.value); step.value=2; success.value=t('codeSent')}catch(e){error.value=e.message==='email_exists'?t('emailExists'):t('registerFailed')}finally{loading.value=false} }
async function verifyCode() { loading.value=true; error.value=''; try{const data=await api.verifyCode(email.value,code.value); localStorage.setItem('access_token',data.access_token); localStorage.setItem('refresh_token',data.refresh_token); localStorage.setItem('role',data.user.role); router.push(data.user.role==='admin'||data.user.role==='super_admin'?'/admin':'/')}catch(e){error.value=t('codeError')}finally{loading.value=false} }
</script>
