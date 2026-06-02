<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside class="sidebar">
        <div class="sidebar-section">主菜单</div>
        <nav class="sidebar-nav">
          <router-link to="/"><span class="nav-icon">&#x25A3;</span> 数据看板</router-link>
          <router-link to="/keys"><span class="nav-icon">&#x1F511;</span> 令牌管理</router-link>
          <router-link to="/usage"><span class="nav-icon">&#x1F4C4;</span> 使用日志</router-link>
          <router-link to="/plans"><span class="nav-icon">&#x1F4B0;</span> 钱包管理</router-link>
        </nav>
        <div class="sidebar-section" style="margin-top:16px">工具</div>
        <nav class="sidebar-nav">
          <router-link to="/playground"><span class="nav-icon">&#x1F4AC;</span> Playground</router-link>
        </nav>
      </aside>
      <main class="page-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import TopNavBar from '../components/TopNavBar.vue'
</script>
