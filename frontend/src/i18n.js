import { ref, computed } from 'vue'

const locale = ref(localStorage.getItem('lang') || 'zh')

const messages = {
  zh: {
    home: '首页',
    console: '控制台',
    marketplace: '模型广场',
    playground: 'Playground',
    dashboard: '数据看板',
    tokens: '令牌管理',
    usage: '使用日志',
    wallet: '钱包管理',
    settings: '个人设置',
    consoleGroup: '控制台',
    personalGroup: '个人中心',
    collapse: '收起侧边栏',
    logout: '退出登录',
    admin: '管理后台',
    profile: '个人设置',
    notifications: '系统通知',
    markAllRead: '全部已读',
    noNotifications: '暂无通知',
    search: '搜索',
    refresh: '刷新',
    theme: '切换主题',
    language: '语言',
  },
  en: {
    home: 'Home',
    console: 'Console',
    marketplace: 'Marketplace',
    playground: 'Playground',
    dashboard: 'Dashboard',
    tokens: 'API Tokens',
    usage: 'Usage Logs',
    wallet: 'Wallet',
    settings: 'Settings',
    consoleGroup: 'Console',
    personalGroup: 'Personal',
    collapse: 'Collapse Sidebar',
    logout: 'Logout',
    admin: 'Admin Panel',
    profile: 'Settings',
    notifications: 'Notifications',
    markAllRead: 'Mark All Read',
    noNotifications: 'No Notifications',
    search: 'Search',
    refresh: 'Refresh',
    theme: 'Toggle Theme',
    language: 'Language',
  },
}

export function useI18n() {
  const t = (key) => messages[locale.value]?.[key] || key

  const toggleLang = () => {
    locale.value = locale.value === 'zh' ? 'en' : 'zh'
    localStorage.setItem('lang', locale.value)
  }

  return { locale, t, toggleLang }
}
