export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.maisb.app'
export const PUBLIC_SITE_URL = import.meta.env.VITE_PUBLIC_SITE_URL || import.meta.env.VITE_PUBLIC_BASE_URL || 'https://maisb.app'
export const DASHBOARD_URL = import.meta.env.VITE_DASHBOARD_URL || import.meta.env.VITE_APP_BASE_URL || 'https://app.maisb.app'
export const PADDLE_ENV = import.meta.env.VITE_PADDLE_ENV || 'sandbox'
export const PADDLE_CLIENT_TOKEN = import.meta.env.VITE_PADDLE_CLIENT_TOKEN || ''
export const PADDLE_PRO_PRICE_ID = import.meta.env.VITE_PADDLE_PRO_PRICE_ID || ''
export const PADDLE_CERTIFY_PRICE_ID = import.meta.env.VITE_PADDLE_CERTIFY_PRICE_ID || ''

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
