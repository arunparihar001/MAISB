import { apiRequest } from './api'
import { PADDLE_CLIENT_TOKEN, PADDLE_ENV } from './config'

export interface CheckoutRequest {
  plan: 'pro' | 'certify'
  email: string
  company?: string
  metadata?: Record<string, unknown>
}

interface CheckoutResponse {
  configured: boolean
  provider: string
  checkout_url?: string
  fallback_request?: {
    request_id: string
    next_step: string
  }
  message?: string
}

export async function beginCheckout(payload: CheckoutRequest): Promise<CheckoutResponse> {
  return apiRequest<CheckoutResponse>('/v1/billing/paddle/checkout-session', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function paddleClientStatus(): string {
  if (!PADDLE_CLIENT_TOKEN) return 'Paddle client token is not configured. Manual upgrade request remains available.'
  return `Paddle client ready (${PADDLE_ENV})`
}
