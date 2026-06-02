<template>
  <header class="topbar">
    <div class="topbar-left">
      <router-link to="/" class="topbar-logo"><LogoIcon :size="28" style="vertical-align:middle;margin-right:8px" /><span>Easy</span>Code</router-link>
      <nav class="topbar-nav">
        <router-link to="/" :class="{ active: isActive('/') }">控制台</router-link>
        <router-link to="/playground" :class="{ active: isActive('/playground') }">Playground</router-link>
      </nav>
    </div>

    <div class="topbar-right">
      <button class="topbar-bell" title="通知">
        &#x1F514;
        <span class="dot"></span>
      </button>

      <div class="topbar-avatar" @click="goAdmin" v-if="isAdmin" title="进入管理端">
        <span style="font-size:11px;color:var(--primary);font-weight:600;margin-right:4px">管理</span>
      </div>

      <div class="topbar-avatar" @click="toggleMenu">
        <div class="avatar-circle">{{ avatarChar }}</div>
        <span class="avatar-name">{{ userName }}</span>
      </div>

      <div v-if="menuOpen" class="dropdown" @click.self="menuOpen = false">
        <div class="dropdown-item" @click="goProfile">个人设置</div>
        <div class="dropdown-item" @click="goAdmin" v-if="isAdmin">管理后台</div>
        <div class="dropdown-divider"></div>
        <div class="dropdown-item danger" @click="logout">退出登录</div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api, isAdmin } from '../api'
import LogoIcon from './LogoIcon.vue'

const router = useRouter()
const route = useRoute()
const userName = ref('')
const menuOpen = ref(false)

const avatarChar = computed(() => userName.value ? userName.value.charAt(0).toUpperCase() : '?')

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

onMounted(async () => {
  try {
    const user = await api.getMe()
    userName.value = user.username || user.email
  } catch (e) { /* */ }
})

function toggleMenu() { menuOpen.value = !menuOpen.value }
function goProfile() { menuOpen.value = false }
function goAdmin() { menuOpen.value = false; router.push('/admin') }

function logout() {
  menuOpen.value = false
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>

<style scoped>
.dropdown {
  position: absolute;
  top: 52px;
  right: 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 0;
  min-width: 140px;
  z-index: 200;
}

.dropdown-item {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
}
.dropdown-item:hover { background: #f5f5f5; }
.dropdown-item.danger { color: var(--danger); }

.dropdown-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}
</style>
