import { createRouter, createWebHistory } from 'vue-router'
import { isAdmin } from './api'

// Layouts
import UserLayout from './layouts/UserLayout.vue'
import AdminLayout from './layouts/AdminLayout.vue'

// User pages
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Dashboard from './pages/Dashboard.vue'
import Keys from './pages/Keys.vue'
import Plans from './pages/Plans.vue'
import Usage from './pages/Usage.vue'
import Playground from './pages/Playground.vue'
import Settings from './pages/Settings.vue'
import Models from './pages/Models.vue'
import ModelDetail from './pages/ModelDetail.vue'

// Admin pages
import AdminDashboard from './pages/AdminDashboard.vue'
import Suppliers from './pages/Suppliers.vue'
import Breakers from './pages/Breakers.vue'
import Users from './pages/Users.vue'
import PlanManager from './pages/PlanManager.vue'
import AdminUsage from './pages/AdminUsage.vue'
import Payments from './pages/Payments.vue'
import Pricing from './pages/Pricing.vue'
import Announcements from './pages/Announcements.vue'
import AdminUserDaily from './pages/AdminUserDaily.vue'
import AdminUserUsage from './pages/AdminUserUsage.vue'

const routes = [
  // Public
  { path: '/login', component: Login },
  { path: '/register', component: Register },

  // User portal
  {
    path: '/',
    component: UserLayout,
    meta: { auth: true },
    children: [
      { path: '', component: Dashboard },
      { path: 'keys', component: Keys },
      { path: 'plans', component: Plans },
      { path: 'usage', component: Usage },
      { path: 'playground', component: Playground },
      { path: 'settings', component: Settings },
      { path: 'models', component: Models },
      { path: 'models/:id', component: ModelDetail },
    ],
  },

  // Admin portal
  {
    path: '/admin',
    component: AdminLayout,
    meta: { auth: true, admin: true },
    children: [
      { path: '', component: AdminDashboard },
      { path: 'suppliers', component: Suppliers },
      { path: 'breakers', component: Breakers },
      { path: 'users', component: Users },
      { path: 'plans', component: PlanManager },
      { path: 'usage', component: AdminUsage },
      { path: 'payments', component: Payments },
      { path: 'pricing', component: Pricing },
      { path: 'announcements', component: Announcements },
      { path: 'user-daily', component: AdminUserDaily },
      { path: 'user-usage', component: AdminUserUsage },
    ],
  },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

function hasToken() {
  return !!localStorage.getItem('access_token')
}

router.beforeEach((to, _from, next) => {
  if (to.meta.auth && !hasToken()) {
    next('/login')
    return
  }
  if (to.meta.admin && !isAdmin()) {
    next('/')
    return
  }
  next()
})

export default router
