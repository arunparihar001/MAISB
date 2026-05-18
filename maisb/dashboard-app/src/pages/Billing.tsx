import { FormEvent, useEffect, useState } from 'react'
import PricingCard from '../components/PricingCard'
import { apiRequest } from '../lib/api'
import { beginCheckout, paddleClientStatus } from '../lib/paddle'

interface PlanResponse {
  plans: { id: string; name: string; price: string; limit: number | null; features: string[] }[]
}

export default function Billing() {
  const [plans, setPlans] = useState<PlanResponse['plans']>([])
  const [message, setMessage] = useState('')
  const [billingForm, setBillingForm] = useState({ email: '', company: '', plan: 'pro' })

  useEffect(() => {
    apiRequest<PlanResponse>('/v1/public/plans').then((data) => setPlans(data.plans)).catch(() => setPlans([]))
  }, [])

  async function manualUpgrade(event: FormEvent) {
    event.preventDefault()
    try {
      const result = await apiRequest<{ request_id: string; next_step: string }>('/v1/billing/upgrade-request', {
        method: 'POST',
        body: JSON.stringify({ ...billingForm, provider: 'manual_invoice' }),
      })
      setMessage(`Manual request ${result.request_id}: ${result.next_step}`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upgrade request failed')
    }
  }

  async function startPaddle() {
    try {
      const result = await beginCheckout({ plan: 'pro', email: billingForm.email, company: billingForm.company })
      if (result.checkout_url) {
        window.location.href = result.checkout_url
        return
      }
      setMessage(result.message || 'Paddle is not configured. Use manual upgrade request.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not start checkout')
    }
  }

  return (
    <div className="page-grid">
      <div className="card">
        <h3>Billing</h3>
        <p className="muted">{paddleClientStatus()}</p>
        <form className="form" onSubmit={manualUpgrade}>
          <input placeholder="Billing email" required value={billingForm.email} onChange={(e) => setBillingForm({ ...billingForm, email: e.target.value })} />
          <input placeholder="Company" value={billingForm.company} onChange={(e) => setBillingForm({ ...billingForm, company: e.target.value })} />
          <select value={billingForm.plan} onChange={(e) => setBillingForm({ ...billingForm, plan: e.target.value })}>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
            <option value="certify">Certify</option>
          </select>
          <button type="submit">Submit manual request</button>
          <button type="button" onClick={startPaddle}>Checkout with Paddle</button>
        </form>
        {message && <p className="notice">{message}</p>}
      </div>
      {plans.map((plan) => (
        <PricingCard key={plan.id} plan={plan} />
      ))}
    </div>
  )
}
