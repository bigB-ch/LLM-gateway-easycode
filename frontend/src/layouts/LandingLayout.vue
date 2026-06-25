<template>
  <div class="app-shell">
    <TopNavBar />
    <main class="landing-main">
      <router-view />
    </main>
    <footer class="app-footer">{{ icpCode }}</footer>
  </div>
</template>

<script setup>
import TopNavBar from '../components/TopNavBar.vue'
const icpCode = '粤ICP备2026078460号-1'
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg);
}

.landing-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
