import { apiRequest } from './api'
import { PADDLE_CERTIFY_PRICE_ID, PADDLE_CLIENT_TOKEN, PADDLE_ENV, PADDLE_PRO_PRICE_ID } from './config'

type CheckoutRequest = {
  api_key?: string
  plan: 'pro' | 'certify'
  email?: string
}

type CheckoutResponse = {
  checkout_url?: string
  checkout?: Record<string, unknown>
  configured?: boolean
  message?: string
}

export async function createCheckoutSession(request: CheckoutRequest): Promise<CheckoutResponse> {
  const priceId = request.plan === 'certify' ? PADDLE_CERTIFY_PRICE_ID : PADDLE_PRO_PRICE_ID
  return apiRequest<CheckoutResponse>('/v1/billing/paddle/checkout-session', {
    method: 'POST',
    body: {
      ...request,
      price_id: priceId,
      paddle_env: PADDLE_ENV,
      paddle_client_token: PADDLE_CLIENT_TOKEN,
    },
  })
}
