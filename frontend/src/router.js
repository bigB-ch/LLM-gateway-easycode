import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Dashboard from './pages/Dashboard.vue'
import Keys from './pages/Keys.vue'
import Plans from './pages/Plans.vue'
import Usage from './pages/Usage.vue'

const routes = [
  { path: '/admin/login', component: Login },
  { path: '/admin/register', component: Register },
  { path: '/admin', component: Dashboard, meta: { auth: true } },
  { path: '/admin/keys', component: Keys, meta: { auth: true } },
  { path: '/admin/plans', component: Plans, meta: { auth: true } },
  { path: '/admin/usage', component: Usage, meta: { auth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/admin' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  if (to.meta.auth && !localStorage.getItem('access_token')) {
    next('/admin/login')
  } else {
    next()
  }
})

export default router
