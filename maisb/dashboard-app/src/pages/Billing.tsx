import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import PricingCard from '../components/PricingCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'
import { createCheckoutSession } from '../lib/paddle'

type Plan = { id: string; name: string; price: string; features: string[] }
type PlansResponse = { plans: Plan[] }
type UsageData = { email?: string; plan: string }
type BillingStatus = { status?: string; request_id?: string; provider?: string; updated_at?: string }

export default function Billing() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<BillingStatus | null>(null)
  const [usage, setUsage] = useState<UsageData | null>(null)

  useEffect(() => {
    const apiKey = getApiKey()
    apiRequest<PlansResponse>('/v1/public/plans').then((r) => setPlans(r.plans)).catch(() => setPlans([]))
    apiRequest<UsageData>(withApiKey('/v1/public/usage', apiKey)).then(setUsage).catch(() => setUsage(null))
    apiRequest<BillingStatus>(withApiKey('/v1/billing/status', apiKey)).then(setStatus).catch(() => setStatus(null))
  }, [])

  const startCheckout = async (plan: 'pro' | 'certify') => {
    setMessage('')
    try {
      const result = await createCheckoutSession({ plan, api_key: getApiKey(), email: usage?.email })
      if (result.checkout_url) {
        window.location.href = result.checkout_url
        return
      }
      setMessage(result.message || 'Paddle is not configured. Please submit a manual upgrade request below.')
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Could not start checkout. Please use manual upgrade request.')
    }
  }

  const submitManual = async (event: FormEvent) => {
    event.preventDefault()
    try {
      await apiRequest('/v1/billing/upgrade-request', {
        method: 'POST',
        body: { email: usage?.email || '', company: '', plan: 'pro', provider: 'manual_invoice', notes: 'Dashboard fallback request' },
      })
      setMessage('Manual upgrade request submitted. Our commercial team will follow up.')
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Unable to submit manual request')
    }
  }

  return (
    <section className="stack">
      <h1>Billing</h1>
      {status?.status ? <p className="notice">Latest billing status: {status.status} ({status.provider || 'n/a'})</p> : null}
      <div className="grid">{plans.map((plan) => <PricingCard key={plan.id} name={plan.name} price={plan.price} features={plan.features} />)}</div>
      <div className="row">
        <button className="btn" onClick={() => startCheckout('pro')}>Upgrade to Pro</button>
        <button className="btn secondary" onClick={() => startCheckout('certify')}>Buy Certify</button>
      </div>
      <form onSubmit={submitManual} className="card form">
        <h3>Manual fallback</h3>
        <p className="muted">If Paddle is unavailable, request manual invoicing.</p>
        <button className="btn secondary" type="submit">Request manual invoice</button>
      </form>
      {message ? <p className="warn">{message}</p> : null}
    </section>
  )
}
