import { clearAuthState, getApiKey, getSessionToken } from './auth'
import { API_BASE_URL } from './config'

export type ApiError = Error & { status?: number }

function networkErrorMessage(method: string, path: string): string {
  return `Network/CORS failure while calling ${method} ${path} at ${API_BASE_URL}`
}

function parseErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback
  const detail = (data as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown; message?: unknown }
    if (typeof first.message === 'string') return first.message
    if (typeof first.msg === 'string') return first.msg
  }
  if (detail && typeof detail === 'object') {
    const message = (detail as { message?: unknown }).message
    if (typeof message === 'string') return message
  }
  const message = (data as { message?: unknown }).message
  if (typeof message === 'string') return message
  const error = (data as { error?: unknown }).error
  if (typeof error === 'string') return error
  return fallback
}

function normalizeFetchError(method: string, path: string): Error {
  const message = networkErrorMessage(method, path)
  return new Error(message)
}

export function buildHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers || {})
  if (init?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const token = getSessionToken()
  const apiKey = getApiKey()
  if (!headers.has('Authorization')) {
    if (token) headers.set('Authorization', `Bearer ${token}`)
    else if (apiKey) headers.set('Authorization', `Bearer ${apiKey}`)
  }

  return headers
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: buildHeaders(init),
    })
  } catch {
    const method = (init?.method || 'GET').toUpperCase()
    throw normalizeFetchError(method, path)
  }

  const raw = await response.text()
  let data: unknown = null
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      data = { message: raw }
    }
  }

  if (response.status === 401) {
    clearAuthState()
  }

  if (!response.ok) {
    const err = new Error(parseErrorMessage(data, `Request failed with HTTP ${response.status}`)) as ApiError
    err.status = response.status
    throw err
  }

  return data as T
}

export async function apiText(path: string, init?: RequestInit): Promise<string> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: buildHeaders(init),
    })
  } catch {
    throw normalizeFetchError('GET', path)
  }
  const raw = await response.text()
  if (!response.ok) {
    const err = new Error(raw || `Request failed with HTTP ${response.status}`) as ApiError
    err.status = response.status
    throw err
  }
  return raw
}

export async function downloadWithAuth(path: string, filename: string): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { headers: buildHeaders() })
  } catch {
    throw normalizeFetchError('GET', path)
  }
  if (!response.ok) {
    throw new Error(`Download failed with HTTP ${response.status}`)
  }
  const blob = await response.blob()
  const href = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(href)
}

export function withAdminKey(path: string, adminKey: string): string {
  const glue = path.includes('?') ? '&' : '?'
  return `${path}${glue}admin_key=${encodeURIComponent(adminKey)}`
}

export function adminHeaders(adminKey: string): HeadersInit {
  return adminKey ? { Authorization: `Bearer ${adminKey}` } : {}
}
