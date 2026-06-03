<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside :class="'sidebar ' + (collapsed ? 'collapsed' : '')">
        <div class="sidebar-section">{{ t('consoleGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/"><span class="nav-icon">&#x25A3;</span> <span>{{ t('dashboard') }}</span></router-link>
          <router-link to="/keys"><span class="nav-icon">&#x1F511;</span> <span>{{ t('tokens') }}</span></router-link>
          <router-link to="/usage"><span class="nav-icon">&#x1F4C4;</span> <span>{{ t('usage') }}</span></router-link>
        </nav>

        <div class="sidebar-section">{{ t('personalGroup') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/plans"><span class="nav-icon">&#x1F4B0;</span> <span>{{ t('wallet') }}</span></router-link>
          <router-link to="/settings"><span class="nav-icon">&#x2699;&#xFE0F;</span> <span>{{ t('settings') }}</span></router-link>
          <router-link to="/playground"><span class="nav-icon">&#x1F4AC;</span> <span>{{ t('playground') }}</span></router-link>
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../i18n'
import TopNavBar from '../components/TopNavBar.vue'

const { t } = useI18n()
const collapsed = ref(false)
</script>
