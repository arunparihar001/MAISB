import { API_BASE_URL } from './config'

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  })

  const raw = await response.text()
  let data: unknown = {}
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      if (response.ok) {
        throw new Error('Unexpected non-JSON response from API')
      }
      throw new Error(raw)
    }
  }
  if (!response.ok) {
    throw new Error((data as { detail?: string })?.detail || 'Request failed')
  }
  return data as T
}

export function withApiKey(path: string, apiKey: string): string {
  const glue = path.includes('?') ? '&' : '?'
  return `${path}${glue}api_key=${encodeURIComponent(apiKey)}`
}
