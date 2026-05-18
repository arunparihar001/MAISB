import { API_BASE_URL } from './config'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function withApiKey(path: string, apiKey: string): string {
  const separator = path.includes('?') ? '&' : '?'
  return `${path}${separator}api_key=${encodeURIComponent(apiKey)}`
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, adminBearer?: string): Promise<T> {
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json')
  if (adminBearer) headers.set('Authorization', `Bearer ${adminBearer}`)

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      throw new ApiError(response.status, text)
    }
  }
  if (!response.ok) {
    const err = payload as { detail?: string; message?: string } | null
    throw new ApiError(response.status, err?.detail || err?.message || `Request failed with status ${response.status}`)
  }
  return payload as T
}
