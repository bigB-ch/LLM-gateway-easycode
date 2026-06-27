<template>
  <header class="topbar">
    <div class="topbar-left">
      <router-link to="/" class="topbar-logo">
        <LogoIcon :size="28" style="vertical-align:middle;margin-right:8px" /><span>Easy</span>Code
      </router-link>
      <nav class="topbar-nav">
        <router-link to="/" exact-active-class="active">{{ t('home') }}</router-link>
        <router-link to="/store" :class="{ active: isStore }">{{ t('store') }}</router-link>
        <router-link to="/custom" :class="{ active: isCustom }">{{ t('customTools') }}</router-link>
        <router-link to="/dashboard" :class="{ active: isConsole }">{{ t('console') }}</router-link>
      </nav>
    </div>

    <div class="topbar-right">
      <template v-if="isLoggedIn">
        <button class="topbar-bell" title="通知" @click.stop="showNoti = !showNoti">
          &#x1F514;
          <span class="bell-badge" v-if="notiCount > 0">{{ notiCount > 99 ? '99+' : notiCount }}</span>
        </button>
        <button class="topbar-icon-btn" title="切换主题" @click="toggleTheme">
          {{ isDark ? '&#x263E;' : '&#x2600;' }}
        </button>
        <div class="topbar-avatar" @click.stop="menuOpen = !menuOpen">
          <div class="avatar-circle">{{ avatarChar }}</div>
          <span class="avatar-name">{{ userName }}</span>
        </div>

        <div v-if="menuOpen" class="topbar-dropdown" @click.stop>
          <div class="dropdown-header">{{ userName }}</div>
          <div class="dropdown-item" @click="goPage('/settings')">&#x2699;&#xFE0F; {{ t('profile') }}</div>
          <div class="dropdown-item" @click="goPage('/keys')">&#x1F511; {{ t('tokens') }}</div>
          <div class="dropdown-item" @click="goPage('/plans')">&#x1F4B0; {{ t('wallet') }}</div>
          <div v-if="isAdminUser" class="dropdown-item" @click="goAdmin">&#x2696;&#xFE0F; {{ t('admin') }}</div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item danger" @click="logout">{{ t('logout') }}</div>
        </div>

        <!-- Notification panel -->
        <div v-if="showNoti" class="noti-panel" @click.stop>
          <div class="noti-header">
            {{ t('notifications') }}
            <button v-if="notifications.length" class="noti-clear" @click="clearAllNoti">{{ t('markAllRead') }}</button>
          </div>
          <div v-if="notifications.length" class="noti-list">
            <div v-for="n in notifications" :key="n.id" class="noti-item" @click="dismissNoti(n.id)">
              <div class="noti-title">{{ n.title }}</div>
              <div class="noti-time">{{ n.time }}</div>
            </div>
          </div>
          <div v-else class="noti-empty">{{ t('noNotifications') }}</div>
        </div>
      </template>
      <template v-else>
        <router-link to="/login" class="topbar-login-btn">登录</router-link>
      </template>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api, isAdmin } from '../api'
import { useI18n } from '../i18n'
import { useTheme } from '../composables/useTheme'
import LogoIcon from './LogoIcon.vue'

const { t } = useI18n()
const { isDark, toggleTheme, initTheme } = useTheme()

const router = useRouter()
const route = useRoute()
const userName = ref('')
const menuOpen = ref(false)
const showNoti = ref(false)
const notiCount = ref(1)
const isAdminUser = computed(() => isAdmin())
const isLoggedIn = computed(() => !!localStorage.getItem('access_token'))

const avatarChar = computed(() => userName.value ? userName.value.charAt(0).toUpperCase() : '?')

const isStore = computed(() => route.path.startsWith('/store'))
const isCustom = computed(() => route.path.startsWith('/custom'))

const isConsole = computed(() => {
  const p = route.path
  return p.startsWith('/dashboard') || p.startsWith('/keys') || p.startsWith('/usage') || p.startsWith('/plans') || p.startsWith('/settings') || p.startsWith('/models')
})

const notifications = ref([])

const ANNOUNCEMENTS_KEY = 'read_announcements'

function getReadIds() {
  try { return JSON.parse(localStorage.getItem(ANNOUNCEMENTS_KEY) || '[]') } catch { return [] }
}
function saveReadId(id) {
  const ids = getReadIds()
  if (!ids.includes(id)) { ids.push(id); localStorage.setItem(ANNOUNCEMENTS_KEY, JSON.stringify(ids)) }
}

onMounted(async () => {
  try {
    const user = await api.getMe()
    userName.value = user.username || user.email
  } catch (e) { /* */ }
  await loadAnnouncements()
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => document.removeEventListener('click', closeMenu))

async function loadAnnouncements() {
  try {
    const res = await api.getAnnouncements()
    const readIds = getReadIds()
    const items = (res.items || []).map(a => ({ ...a, title: a.content, read: readIds.includes(a.id) }))
    notifications.value = items
    notiCount.value = items.filter(a => !a.read).length
  } catch (e) { /* keep old notifications on error */ }
}

function closeMenu() { menuOpen.value = false; showNoti.value = false }
function dismissNoti(id) {
  saveReadId(id)
  notifications.value = notifications.value.filter(n => n.id !== id)
  notiCount.value = Math.max(0, notiCount.value - 1)
}
function clearAllNoti() {
  notifications.value.forEach(n => saveReadId(n.id))
  notifications.value = []
  notiCount.value = 0
}
function goPage(p) { router.push(p); menuOpen.value = false }
function goAdmin() { router.push('/admin'); menuOpen.value = false }
// Theme is managed by the shared useTheme() composable (imported above)
initTheme()

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('role')
  router.push('/')
}
</script>

<style scoped>
.topbar-dropdown {
  position: absolute;
  top: 52px; right: 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  min-width: 180px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  z-index: 200;
  padding: 6px 0;
}
.dropdown-header {
  padding: 8px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}
.dropdown-item {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
}
.dropdown-item:hover { background: #f5f5f5; }
.dropdown-item.danger { color: var(--danger); }
.dropdown-divider { height: 1px; background: var(--border); margin: 4px 0; }

.bell-badge {
  position: absolute;
  top: -2px; right: -2px;
  min-width: 16px; height: 16px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  line-height: 1;
}

.noti-panel {
  position: absolute;
  top: 52px; right: 120px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 320px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  z-index: 200;
  padding: 0;
}
.noti-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.noti-clear {
  font-size: 12px;
  font-weight: 400;
  color: var(--primary);
  background: none;
  border: none;
  cursor: pointer;
}
.noti-clear:hover { text-decoration: underline; }
.noti-list { max-height: 280px; overflow-y: auto; }
.noti-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
}
.noti-item:hover { background: #f8f9fb; }
.noti-title { font-size: 13px; color: var(--text); line-height: 1.5; }
.noti-time { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.noti-empty { padding: 32px 16px; text-align: center; color: var(--text-muted); font-size: 13px; }

.topbar-login-btn {
  padding: 6px 20px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  background: var(--primary);
  color: #fff;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
  line-height: 1.6;
}
.topbar-login-btn:hover {
  background: var(--primary-hover);
}
</style>
