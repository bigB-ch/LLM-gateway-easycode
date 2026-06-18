import { ref, computed } from 'vue'
import { darkTheme } from 'naive-ui'

const isDark = ref(false)

export function useTheme() {
  const theme = computed(() => (isDark.value ? darkTheme : null))

  function initTheme() {
    const saved = localStorage.getItem('theme')
    isDark.value =
      saved === 'dark' ||
      (!saved && window.matchMedia?.('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  return { isDark, theme, initTheme, toggleTheme }
}
