import { API_BASE_URL } from './config'

function withQuery(url: string, query?: Record<string, string | undefined>) {
  if (!query) return url
  const params = new URLSearchParams()
  Object.entries(query).forEach(([k, v]) => {
    if (v) params.set(k, v)
  })
  return params.toString() ? `${url}?${params}` : url
}

export async function apiGet<T>(
  path: string,
  query?: Record<string, string | undefined>,
  headers?: Record<string, string>,
): Promise<T> {
  const response = await fetch(withQuery(`${API_BASE_URL}${path}`, query), { headers })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

export async function apiPost<T>(path: string, body: unknown, headers?: Record<string, string>): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}
