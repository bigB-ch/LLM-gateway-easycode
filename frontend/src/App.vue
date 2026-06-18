<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <router-view />
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
} from 'naive-ui'
import { useTheme } from './composables/useTheme'
import { themeOverrides } from './styles/naive-theme-overrides'

const { theme, initTheme } = useTheme()
onMounted(initTheme)
</script>
