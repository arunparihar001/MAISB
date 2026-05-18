const API_KEY_STORAGE_KEY = 'maisb_api_key'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'

export function setApiKey(value: string): void {
  const key = value.trim()
  if (key) localStorage.setItem(API_KEY_STORAGE_KEY, key)
}

export function getApiKey(): string {
  return (localStorage.getItem(API_KEY_STORAGE_KEY) || '').trim()
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function setAdminKey(value: string): void {
  const key = value.trim()
  if (key) localStorage.setItem(ADMIN_KEY_STORAGE_KEY, key)
}

export function getAdminKey(): string {
  return (localStorage.getItem(ADMIN_KEY_STORAGE_KEY) || '').trim()
}

export function clearAdminKey(): void {
  localStorage.removeItem(ADMIN_KEY_STORAGE_KEY)
}

export function maskKey(value: string): string {
  if (!value) return 'Not set'
  if (value.length < 12) return `${value.slice(0, 4)}****`
  return `${value.slice(0, 10)}****${value.slice(-4)}`
}
