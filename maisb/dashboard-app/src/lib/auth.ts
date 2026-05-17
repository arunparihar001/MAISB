let runtimeApiKey = ''

export function getApiKey(): string {
  if (runtimeApiKey) return runtimeApiKey
  return new URLSearchParams(window.location.search).get('api_key') || ''
}

export function setApiKey(value: string): void {
  runtimeApiKey = value || ''
}
