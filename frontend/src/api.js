const BASE = '/admin/api'

function getToken() {
  return localStorage.getItem('access_token')
}

export function getRole() {
  return localStorage.getItem('role')
}

export function isAdmin() {
  const role = getRole()
  return role === 'admin' || role === 'super_admin'
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (res.status === 401 && path !== '/auth/login') {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('role')
    window.location = '/login'
    throw new Error('unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'request_failed' }))
    throw new Error(err.error || err.detail?.error || 'request_failed')
  }
  return res.json()
}

export const api = {
  login: (login, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ login, password }) }),

  register: (username, email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ username, email, password }) }),

  sendCode: (email) =>
    request('/auth/send-code', { method: 'POST', body: JSON.stringify({ email }) }),

  verifyCode: (email, code) =>
    request('/auth/verify-code', { method: 'POST', body: JSON.stringify({ email, code }) }),

  getMe: () => request('/auth/me'),

  getDashboard: () => request('/reports/dashboard'),

  getTrend: (days = 7) => request(`/reports/trend?days=${days}`),

  getUsage: (page = 1) => request(`/reports/usage?page=${page}`),

  createKey: (name, rateLimit = 60) =>
    request('/keys', { method: 'POST', body: JSON.stringify({ name, rate_limit: rateLimit }) }),

  listKeys: () => request('/keys'),

  revokeKey: (id) => request(`/keys/${id}/revoke`, { method: 'POST' }),

  getPlans: () => request('/plans'),

  purchasePlan: (planId) => request(`/plans/${planId}/purchase`, { method: 'POST' }),

  changePassword: (oldPassword, newPassword) =>
    request('/auth/password', { method: 'PUT', body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }) }),
}
