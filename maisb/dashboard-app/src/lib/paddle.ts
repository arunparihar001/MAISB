import { apiRequest } from './api'

export type PaddleCheckoutResponse = {
  checkout_url: string
  provider: string
  request_id: string
}

export function createPaddleCheckout(email: string, plan: string) {
  return apiRequest<PaddleCheckoutResponse>('/v1/billing/paddle/checkout-link', {
    method: 'POST',
    body: JSON.stringify({ email, plan }),
  })
}
