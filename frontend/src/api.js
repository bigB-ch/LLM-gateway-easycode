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
    // Only redirect if user had a token (session expired), not for anonymous visitors
    if (token) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('role')
      window.location = '/'
    }
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

  getModels: async () => {
    const res = await fetch('/v1/models')
    return res.json()
  },

  getTrend: (days = 7) => request(`/reports/trend?days=${days}`),

  getUsage: (page = 1, dateFrom, dateTo) => {
    const params = new URLSearchParams({ page: String(page) })
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    return request(`/reports/usage?${params}`)
  },

  createKey: (name, rateLimit = 60, opts = {}) =>
    request('/keys', { method: 'POST', body: JSON.stringify({
      name, rate_limit: rateLimit,
      token_group: opts.token_group || null,
      token_quota: opts.token_quota || null,
      ip_whitelist: opts.ip_whitelist || null,
      model_allowlist: opts.model_allowlist || null,
      expire_days: opts.expire_days || null,
      count: opts.count || 1,
    }) }),

  listKeys: () => request('/keys'),

  revokeKey: (id) => request(`/keys/${id}/revoke`, { method: 'POST' }),

  revealKey: (id) => request(`/keys/${id}/reveal`, { method: 'POST' }),

  deleteKey: (id) => request(`/keys/${id}`, { method: 'DELETE' }),

  getPlans: () => request('/plans'),

  purchasePlan: (planId) => request(`/plans/${planId}/purchase`, { method: 'POST' }),

  changePassword: (oldPassword, newPassword) =>
    request('/auth/password', { method: 'PUT', body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }) }),

  forgotPassword: (email) =>
    request('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),

  resetPassword: (email, code, newPassword) =>
    request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ email, code, new_password: newPassword }) }),

  // ── Admin ──
  getAdminDashboard: () => request('/reports/admin-dashboard'),

  listUsers: (cursor, limit = 50) => {
    const params = new URLSearchParams({ limit: String(limit) })
    if (cursor) params.set('cursor', cursor)
    return request(`/users?${params}`)
  },

  toggleUser: (userId, action) =>
    request(`/users/${userId}/${action}`, { method: 'POST' }),

  topupUser: (userId, amountYuan) =>
    request(`/users/${userId}/topup`, { method: 'POST', body: JSON.stringify({ amount_yuan: amountYuan }) }),

  createPlan: (name, tokenQuota, price, durationDays, description) =>
    request('/plans', { method: 'POST', body: JSON.stringify({ name, token_quota: tokenQuota, price, duration_days: durationDays, description }) }),

  getAllUsage: (page = 1, pageSize = 20) =>
    request(`/reports/all-usage?page=${page}&page_size=${pageSize}`),

  getAdminTrend: (days = 7) => request(`/reports/admin-trend?days=${days}`),

  getAdminDaily: (page = 1, pageSize = 14) =>
    request(`/reports/admin-daily?page=${page}&page_size=${pageSize}`),

  getUserDaily: (page = 1, pageSize = 20, dateFrom, dateTo) => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    return request(`/reports/user-daily?${params}`)
  },

  getUserUsageSummary: (page = 1, pageSize = 20) =>
    request(`/reports/user-usage-summary?page=${page}&page_size=${pageSize}`),

  getUserModelUsage: (userId, page = 1, pageSize = 20) =>
    request(`/reports/user-model-usage/${userId}?page=${page}&page_size=${pageSize}`),

  getAnnouncements: () => request('/system/announcements'),

  listAnnouncements: () => request('/system/admin/announcements'),

  createAnnouncement: (content) =>
    request('/system/admin/announcements', { method: 'POST', body: JSON.stringify({ content }) }),

  updateAnnouncement: (id, content) =>
    request(`/system/admin/announcements/${id}`, { method: 'PUT', body: JSON.stringify({ content }) }),

  deleteAnnouncement: (id) =>
    request(`/system/admin/announcements/${id}`, { method: 'DELETE' }),

  getFAQ: () => request('/system/faq'),

  recharge: (amountYuan, method = 'alipay', txnId = null) =>
    request('/plans/recharge', { method: 'POST', body: JSON.stringify({ amount_yuan: amountYuan, method, txn_id: txnId }) }),

  alipayRecharge: (amountYuan) =>
    request('/plans/recharge/alipay', { method: 'POST', body: JSON.stringify({ amount_yuan: amountYuan }) }),

  queryAlipayPayment: (outTradeNo) =>
    request(`/plans/recharge/alipay/query?out_trade_no=${outTradeNo}`, { method: 'POST' }),

  getPaymentConfig: () => request('/system/payment-config'),

  savePaymentConfig: (config) =>
    request('/system/payment-config', { method: 'PUT', body: JSON.stringify(config) }),

  getPricing: () => request('/system/pricing'),

  savePricing: (data) =>
    request('/system/pricing', { method: 'PUT', body: JSON.stringify(data) }),

  getPendingPayments: () => request('/plans/payments/pending'),

  verifyPayment: (paymentId, approved) =>
    request(`/plans/payments/${paymentId}/verify`, { method: 'POST', body: JSON.stringify({ approved }) }),

  redeemCode: (code) =>
    request('/plans/redeem', { method: 'POST', body: JSON.stringify({ code }) }),

  getRechargeHistory: () => request('/plans/recharge-history'),

  getSettings: () => request('/users/me/settings'),

  saveSettings: (settings) =>
    request('/users/me/settings', { method: 'PUT', body: JSON.stringify({ settings }) }),

  // ── Store / Marketplace ──
  listProducts: (category) => {
    const params = category ? `?category=${category}` : ''
    return request(`/store/products${params}`)
  },

  getProduct: (id) => request(`/store/products/${id}`),

  createOrder: (productId, method = 'alipay') =>
    request('/store/orders', { method: 'POST', body: JSON.stringify({ product_id: productId, method }) }),

  queryOrder: (orderId) =>
    request(`/store/orders/${orderId}/query`, { method: 'POST' }),

  listOrders: () => request('/store/orders'),

  getDownloadUrl: (orderId) =>
    request(`/store/orders/${orderId}/download`),

  // ── Admin Store ──
  adminListProducts: (category, status) => {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (status) params.set('status', status)
    return request(`/store/admin/products?${params}`)
  },

  adminCreateProduct: (data) =>
    request('/store/admin/products', { method: 'POST', body: JSON.stringify(data) }),

  adminUpdateProduct: (id, data) =>
    request(`/store/admin/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  adminDeleteProduct: (id) =>
    request(`/store/admin/products/${id}`, { method: 'DELETE' }),
}
