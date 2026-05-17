const API_KEY_STORAGE_KEY = 'maisb_api_key'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || ''
}

export function setApiKey(value: string): void {
  const trimmed = value.trim()
  if (!trimmed) return
  localStorage.setItem(API_KEY_STORAGE_KEY, trimmed)
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function getAdminKey(): string {
  return localStorage.getItem(ADMIN_KEY_STORAGE_KEY) || ''
}

export function setAdminKey(value: string): void {
  const trimmed = value.trim()
  if (!trimmed) return
  localStorage.setItem(ADMIN_KEY_STORAGE_KEY, trimmed)
}

export function clearAdminKey(): void {
  localStorage.removeItem(ADMIN_KEY_STORAGE_KEY)
}
