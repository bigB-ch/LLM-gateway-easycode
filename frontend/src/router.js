import { createRouter, createWebHistory } from 'vue-router'
import { isAdmin } from './api'

// Layouts
import LandingLayout from './layouts/LandingLayout.vue'
import UserLayout from './layouts/UserLayout.vue'
import AdminLayout from './layouts/AdminLayout.vue'

// User pages
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import LandingPage from './pages/LandingPage.vue'
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

// Marketplace pages
import StorePage from './pages/StorePage.vue'
import StoreDetail from './pages/StoreDetail.vue'
import OrdersPage from './pages/OrdersPage.vue'
import CustomTools from './pages/CustomTools.vue'
import CustomDetail from './pages/CustomDetail.vue'
import AdminProducts from './pages/AdminProducts.vue'

const routes = [
  // Public
  { path: '/login', component: Login },
  { path: '/register', component: Register },

  // Landing page (no sidebar)
  {
    path: '/',
    component: LandingLayout,
    meta: { auth: true },
    children: [
      { path: '', component: LandingPage },
      { path: 'store', component: StorePage },
      { path: 'store/:id', component: StoreDetail },
      { path: 'orders', component: OrdersPage },
      { path: 'custom', component: CustomTools },
      { path: 'custom/:id', component: CustomDetail },
    ],
  },

  // User portal (with sidebar)
  {
    path: '/',
    component: UserLayout,
    meta: { auth: true },
    children: [
      { path: 'dashboard', component: Dashboard },
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
      { path: 'products', component: AdminProducts },
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
