<template>
  <div class="app-shell">
    <TopNavBar />
    <div class="app-body">
      <aside class="sidebar">
        <div style="padding:8px 16px 4px;display:flex;align-items:center;gap:6px">
          <a href="/" style="font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:4px">&#x2190; {{ t('adminBackToUser') }}</a>
        </div>
        <div class="sidebar-section" style="margin-top:8px">{{ t('adminPanel') }}</div>
        <nav class="sidebar-nav">
          <router-link to="/admin"><span class="nav-icon">&#x25A3;</span> {{ t('adminDashboard') }}</router-link>
          <router-link to="/admin/suppliers"><span class="nav-icon">&#x2699;&#xFE0F;</span> {{ t('adminSuppliers') }}</router-link>
          <router-link to="/admin/breakers"><span class="nav-icon">&#x26A1;</span> {{ t('adminBreakers') }}</router-link>
          <router-link to="/admin/users"><span class="nav-icon">&#x1F465;</span> {{ t('adminUsers') }}</router-link>
          <router-link to="/admin/plans"><span class="nav-icon">&#x1F4E6;</span> {{ t('adminPlans') }}</router-link>
          <router-link to="/admin/usage"><span class="nav-icon">&#x1F4CA;</span> {{ t('adminUsage') }}</router-link>
          <router-link to="/admin/payments"><span class="nav-icon">&#x1F4B3;</span> 支付审核</router-link>
          <router-link to="/admin/pricing"><span class="nav-icon">&#x1F4C8;</span> 价格管理</router-link>
          <router-link to="/admin/announcements"><span class="nav-icon">&#x1F4E2;</span> 公告管理</router-link>
        </nav>
      </aside>
      <main class="page-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from '../i18n'
import TopNavBar from '../components/TopNavBar.vue'

const { t } = useI18n()
</script>
