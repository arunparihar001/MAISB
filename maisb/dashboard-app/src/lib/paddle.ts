import { apiRequest } from './api'

export type PaddleCheckoutResponse = {
  provider: 'paddle'
  provisioning: 'pending_webhook_confirmation'
  checkout_url?: string
  checkout_config?: Record<string, unknown>
  price_id?: string
  plan: 'pro' | 'certify'
  message?: string
}

export async function createPaddleCheckout(input: {
  email: string
  company?: string
  plan: 'pro' | 'certify'
  success_url?: string
  cancel_url?: string
}): Promise<PaddleCheckoutResponse> {
  return apiRequest<PaddleCheckoutResponse>('/v1/billing/paddle/checkout-session', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}
