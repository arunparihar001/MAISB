export type StoredProfile = {
  id: string
  name?: string
  email: string
  company?: string
  use_case?: string
  verified: boolean
  plan?: string
}

const AUTH_TOKEN_STORAGE_KEY = 'maisb_auth_token'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'
const PROFILE_STORAGE_KEY = 'maisb_profile'
const PLAN_STORAGE_KEY = 'maisb_selected_plan'
const API_KEY_EXISTS_STORAGE_KEY = 'maisb_api_key_exists'
const EMAIL_STORAGE_KEY = 'maisb_email'
let transientApiKey = ''

export function setSessionToken(value: string): void {
  localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, value.trim())
}

export function getSessionToken(): string {
  return localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || ''
}

export function clearSessionToken(): void {
  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
}

export function setStoredProfile(profile: StoredProfile): void {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile))
}

export function getStoredProfile(): StoredProfile | null {
  const raw = localStorage.getItem(PROFILE_STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as StoredProfile
  } catch {
    return null
  }
}

export function clearStoredProfile(): void {
  localStorage.removeItem(PROFILE_STORAGE_KEY)
}

export function setSelectedPlan(value: string): void {
  localStorage.setItem(PLAN_STORAGE_KEY, value.trim().toLowerCase())
}

export function getSelectedPlan(): string {
  return localStorage.getItem(PLAN_STORAGE_KEY) || ''
}

export function clearSelectedPlan(): void {
  localStorage.removeItem(PLAN_STORAGE_KEY)
}

export function setApiKey(value: string): void {
  transientApiKey = value.trim()
  localStorage.setItem(API_KEY_EXISTS_STORAGE_KEY, '1')
}

export function getApiKey(): string {
  return transientApiKey
}

export function clearApiKey(): void {
  transientApiKey = ''
}

export function setApiKeyExists(value: boolean): void {
  localStorage.setItem(API_KEY_EXISTS_STORAGE_KEY, value ? '1' : '0')
}

export function getApiKeyExists(): boolean {
  return localStorage.getItem(API_KEY_EXISTS_STORAGE_KEY) === '1'
}

export function setStoredEmail(value: string): void {
  localStorage.setItem(EMAIL_STORAGE_KEY, value.trim())
}

export function getStoredEmail(): string {
  return localStorage.getItem(EMAIL_STORAGE_KEY) || ''
}

export function clearStoredEmail(): void {
  localStorage.removeItem(EMAIL_STORAGE_KEY)
}

export function clearAuthState(): void {
  clearSessionToken()
  clearStoredProfile()
  clearSelectedPlan()
  clearStoredEmail()
  clearApiKey()
  setApiKeyExists(false)
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
