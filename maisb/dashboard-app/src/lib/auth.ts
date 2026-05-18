const API_KEY_STORAGE_KEY = 'maisb_api_key'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'

export function setApiKey(value: string): void {
  localStorage.setItem(API_KEY_STORAGE_KEY, value.trim())
}

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || ''
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function setAdminKey(value: string): void {
  localStorage.setItem(ADMIN_KEY_STORAGE_KEY, value.trim())
}

export function getAdminKey(): string {
  return localStorage.getItem(ADMIN_KEY_STORAGE_KEY) || ''
}

export function clearAdminKey(): void {
  localStorage.removeItem(ADMIN_KEY_STORAGE_KEY)
}

export function maskSecret(value: string): string {
  if (!value) return 'Not connected'
  if (value.length <= 12) return '••••'
  return `${value.slice(0, 10)}••••${value.slice(-4)}`
}
