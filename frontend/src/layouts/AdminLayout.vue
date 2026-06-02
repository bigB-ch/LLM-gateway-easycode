<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside class="sidebar">
        <div style="padding:8px 16px 4px;display:flex;align-items:center;gap:6px">
          <a href="/" style="font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:4px">&#x2190; 返回用户端</a>
        </div>
        <div class="sidebar-section" style="margin-top:8px">管理后台</div>
        <nav class="sidebar-nav">
          <router-link to="/admin"><span class="nav-icon">&#x25A3;</span> 数据看板</router-link>
          <router-link to="/admin/suppliers"><span class="nav-icon">&#x2699;&#xFE0F;</span> 供应商管理</router-link>
          <router-link to="/admin/breakers"><span class="nav-icon">&#x26A1;</span> 熔断器监控</router-link>
          <router-link to="/admin/users"><span class="nav-icon">&#x1F465;</span> 用户管理</router-link>
          <router-link to="/admin/plans"><span class="nav-icon">&#x1F4E6;</span> 套餐管理</router-link>
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
