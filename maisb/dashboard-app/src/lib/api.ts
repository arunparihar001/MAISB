import { clearApiKey, getApiKey } from './auth'
import { API_BASE_URL } from './config'

export type ApiError = Error & { status?: number }

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers || {})
  if (init?.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

  // Inject Bearer token automatically if a key is stored
  const key = getApiKey()
  if (key && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${key}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  const raw = await response.text()
  let data: unknown = {}
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      if (response.ok) throw new Error('Unexpected non-JSON response from API')
      const err = new Error(raw || `Request failed with HTTP ${response.status}`) as ApiError
      err.status = response.status
      throw err
    }
  }

  if (response.status === 401) {
    // Clear stale key on 401
    clearApiKey()
    const detail = (data as { detail?: string; error?: string; message?: string })?.detail ||
      `Request failed with HTTP ${response.status}`
    const err = new Error(detail) as ApiError
    err.status = response.status
    throw err
  }

  if (!response.ok) {
    const detail = (data as { detail?: string; error?: string; message?: string })?.detail ||
      (data as { detail?: string; error?: string; message?: string })?.error ||
      (data as { detail?: string; error?: string; message?: string })?.message ||
      `Request failed with HTTP ${response.status}`
    const err = new Error(detail) as ApiError
    err.status = response.status
    throw err
  }

  return data as T
}

export function withAdminKey(path: string, adminKey: string): string {
  const glue = path.includes('?') ? '&' : '?'
  return `${path}${glue}admin_key=${encodeURIComponent(adminKey)}`
}

export function adminHeaders(adminKey: string): HeadersInit {
  return adminKey ? { Authorization: `Bearer ${adminKey}` } : {}
}
