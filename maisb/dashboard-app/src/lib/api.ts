import { API_BASE_URL } from './config'

export function withApiKey(path: string, apiKey: string): string {
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}api_key=${encodeURIComponent(apiKey.trim())}`
}

type ApiRequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  const text = await response.text()
  let data: Record<string, unknown> = {}
  if (text) {
    try {
      data = JSON.parse(text) as Record<string, unknown>
    } catch {
      data = { detail: text }
    }
  }

  if (!response.ok) {
    const detail = (data && (data.detail || data.message || data.error)) || response.statusText || 'Request failed'
    throw new Error(`${response.status}: ${detail}`)
  }

  return data as T
}
