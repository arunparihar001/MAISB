const KEY = 'maisb_api_key'

export function getApiKey(): string {
  return localStorage.getItem(KEY) || ''
}

export function setApiKey(value: string): void {
  if (!value) {
    localStorage.removeItem(KEY)
    return
  }
  localStorage.setItem(KEY, value)
}
