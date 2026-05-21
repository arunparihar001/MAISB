const API_KEY_STORAGE_KEY = 'maisb_api_key'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'
const USER_EMAIL_STORAGE_KEY = 'userEmail'
const KEY_ID_STORAGE_KEY = 'keyId'

export function setApiKey(value: string): void {
  localStorage.setItem(API_KEY_STORAGE_KEY, value.trim())
}

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || ''
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function setUserEmail(value: string): void {
  localStorage.setItem(USER_EMAIL_STORAGE_KEY, value.trim())
}

export function getUserEmail(): string {
  return localStorage.getItem(USER_EMAIL_STORAGE_KEY) || ''
}

export function clearUserEmail(): void {
  localStorage.removeItem(USER_EMAIL_STORAGE_KEY)
}

export function setKeyId(value: string): void {
  localStorage.setItem(KEY_ID_STORAGE_KEY, value.trim())
}

export function getKeyId(): string {
  return localStorage.getItem(KEY_ID_STORAGE_KEY) || ''
}

export function clearKeyId(): void {
  localStorage.removeItem(KEY_ID_STORAGE_KEY)
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
