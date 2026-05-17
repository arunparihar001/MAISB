const API_KEY_STORAGE_KEY = 'maisb_api_key'
const ADMIN_KEY_STORAGE_KEY = 'maisb_admin_key'

function encodeSecret(value: string): string {
  const bytes = new TextEncoder().encode(value)
  let binary = ''
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return btoa(binary)
}

function decodeSecret(value: string): string {
  try {
    const binary = atob(value)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i)
    }
    return new TextDecoder().decode(bytes)
  } catch {
    return ''
  }
}

export function getApiKey(): string {
  const raw = localStorage.getItem(API_KEY_STORAGE_KEY) || ''
  return decodeSecret(raw)
}

export function setApiKey(value: string): void {
  const trimmed = value.trim()
  if (!trimmed) {
    localStorage.removeItem(API_KEY_STORAGE_KEY)
    return
  }
  localStorage.setItem(API_KEY_STORAGE_KEY, encodeSecret(trimmed))
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function getAdminKey(): string {
  const raw = localStorage.getItem(ADMIN_KEY_STORAGE_KEY) || ''
  return decodeSecret(raw)
}

export function setAdminKey(value: string): void {
  const trimmed = value.trim()
  if (!trimmed) {
    localStorage.removeItem(ADMIN_KEY_STORAGE_KEY)
    return
  }
  localStorage.setItem(ADMIN_KEY_STORAGE_KEY, encodeSecret(trimmed))
}

export function clearAdminKey(): void {
  localStorage.removeItem(ADMIN_KEY_STORAGE_KEY)
}
