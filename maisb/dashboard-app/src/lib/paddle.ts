import { apiPost } from './api'

export async function createPaddleCheckout(email: string, plan: 'pro' | 'certify') {
  return apiPost('/v1/billing/paddle/checkout-session', { email, plan })
}
