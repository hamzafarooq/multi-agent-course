export const API_BASE = 'http://localhost:3001'

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message || `Request failed (${status})`)
    this.status = status
    this.code = body?.error
  }
}

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, { error: 'network_error', message: 'Could not reach the server on port 3001.' })
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

export function createApi(token) {
  return {
    signup: (email, password) => request('/auth/signup', { method: 'POST', body: { email, password } }),
    login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password } }),
    me: () => request('/auth/me', { token }),

    getMySite: () => request('/me/site', { token }),
    createSite: (fields) => request('/me/site', { method: 'POST', body: fields, token }),
    updateSite: (fields) => request('/me/site', { method: 'PUT', body: fields, token }),

    listMyPosts: () => request('/me/posts', { token }),
    createPost: (fields) => request('/me/posts', { method: 'POST', body: fields, token }),
    getMyPost: (id) => request(`/me/posts/${id}`, { token }),
    updatePost: (id, fields) => request(`/me/posts/${id}`, { method: 'PUT', body: fields, token }),
    publishPost: (id) => request(`/me/posts/${id}/publish`, { method: 'POST', body: {}, token }),
    unpublishPost: (id) => request(`/me/posts/${id}/unpublish`, { method: 'POST', body: {}, token }),

    getSite: (slug) => request(`/sites/${slug}`),
    getSitePosts: (slug) => request(`/sites/${slug}/posts`),
    getSitePost: (slug, postSlug) => request(`/sites/${slug}/posts/${postSlug}`),
    joinSite: (slug, email) => request(`/sites/${slug}/members`, { method: 'POST', body: { email } }),
    ask: (slug, question) => request(`/sites/${slug}/ask`, { method: 'POST', body: { question } }),
  }
}
