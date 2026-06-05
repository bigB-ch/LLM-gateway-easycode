function getToken() {
  return localStorage.getItem('access_token')
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(path, { ...options, headers })
  if (res.status === 401) {
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

export const gatewayApi = {
  listSuppliers: () => request('/gateway/admin/suppliers'),

  upsertSupplier: (provider, apiKey, baseUrl, balance = 0) =>
    request('/gateway/admin/suppliers', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl, balance }),
    }),

  deleteSupplier: (provider) =>
    request(`/gateway/admin/suppliers/${provider}`, { method: 'DELETE' }),

  healthCheck: (provider) =>
    request(`/gateway/admin/suppliers/${provider}/health`, { method: 'POST' }),

  checkBalance: (provider) =>
    request(`/gateway/admin/suppliers/${provider}/balance`, { method: 'POST' }),

  listCircuitBreakers: () => request('/gateway/admin/circuit-breakers'),

  resetCircuitBreaker: (provider) =>
    request(`/gateway/admin/circuit-breakers/${provider}/reset`, { method: 'POST' }),

  listModels: () => fetch('/v1/models').then(r => r.json()),

  listModelCatalog: () => request('/gateway/admin/models'),

  chat: (model, messages, temperature, maxTokens) =>
    request('/gateway/admin/chat', {
      method: 'POST',
      body: JSON.stringify({ model, messages, temperature, max_tokens: maxTokens }),
    }),
}
