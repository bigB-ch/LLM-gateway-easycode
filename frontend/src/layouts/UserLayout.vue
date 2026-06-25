<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside :class="['sidebar', collapsed && 'collapsed']">
        <div class="sidebar-section">{{ t('consoleGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/"><span>{{ t('home') }}</span></router-link>
          <router-link to="/dashboard"><span>{{ t('dashboard') }}</span></router-link>
          <router-link to="/models"><span>{{ t('marketplace') }}</span></router-link>
          <router-link to="/usage"><span>{{ t('usage') }}</span></router-link>
          <router-link to="/keys"><span>{{ t('tokens') }}</span></router-link>
          <router-link to="/playground"><span>{{ t('playground') }}</span></router-link>
        </nav>
        <div class="sidebar-section">{{ t('personalGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/plans"><span>{{ t('wallet') }}</span></router-link>
          <router-link to="/settings"><span>{{ t('settings') }}</span></router-link>
        </nav>
        <div class="sidebar-collapse-btn" @click="collapsed = !collapsed">
          <span class="collapse-icon">&#x00AB;</span>
          <span class="sidebar-collapse-text">{{ t('collapse') }}</span>
        </div>
      </aside>
      <main class="page-main">
        <router-view />
      </main>
    </div>
    <footer class="app-footer">{{ icpCode }}</footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../i18n'
import TopNavBar from '../components/TopNavBar.vue'
const { t } = useI18n()
const collapsed = ref(false)
const icpCode = '粤ICP备2026078460号-1'
</script>

<style scoped>
.page-main { background: var(--page-bg); }
</style>
