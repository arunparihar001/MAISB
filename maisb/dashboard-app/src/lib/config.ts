export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.maisb.app'
export const PUBLIC_BASE_URL = import.meta.env.VITE_PUBLIC_BASE_URL || 'https://maisb.app'
export const APP_BASE_URL = import.meta.env.VITE_APP_BASE_URL || 'https://app.maisb.app'

const appHosts = new Set(['app.maisb.app', 'localhost', '127.0.0.1'])
const publicHosts = new Set(['maisb.app', 'www.maisb.app'])

export function getHostname(): string {
  if (typeof window === 'undefined') return ''
  return window.location.hostname
}

export function isAppHost(): boolean {
  return appHosts.has(getHostname())
}

export function isPublicHost(): boolean {
  return publicHosts.has(getHostname())
}
