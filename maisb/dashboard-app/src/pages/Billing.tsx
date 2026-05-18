import { useEffect, useState } from 'react'
import PricingCard from '../components/PricingCard'
import { apiRequest } from '../lib/api'
import { createPaddleCheckout } from '../lib/paddle'
import { getApiKey } from '../lib/auth'

type Plan = { id: string; name: string; price: string; features: string[] }
type PlansResponse = { plans: Plan[] }

export default function Billing() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')

  useEffect(() => {
    apiRequest<PlansResponse>('/v1/public/plans').then((data) => setPlans(data.plans || []))
  }, [])

  const requestUpgrade = async (plan: string) => {
    setMessage('')
    if (!email.trim()) {
      setMessage('Billing email is required')
      return
    }
    const apiKey = getApiKey()
    try {
      const response = await apiRequest<{ status: string; request_id: string }>('/v1/billing/upgrade-request', {
        method: 'POST',
        body: JSON.stringify({ email, company, plan, provider: 'manual_invoice', metadata: { api_key: apiKey ? 'stored' : 'missing' } }),
      })
      setMessage(`Upgrade request submitted: ${response.request_id}`)
    } catch (error) {
      setMessage((error as Error).message)
    }
  }

  const startPaddle = async () => {
    if (!email.trim()) {
      setMessage('Billing email is required')
      return
    }
    try {
      const data = await createPaddleCheckout(email, 'pro')
      window.location.href = data.checkout_url
    } catch (error) {
      setMessage((error as Error).message)
    }
  }

  return (
    <div className="stack">
      <h2>Billing</h2>
      <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Billing email" />
      <input value={company} onChange={(event) => setCompany(event.target.value)} placeholder="Company" />
      <div className="grid">
        {plans.map((plan) => (
          <div key={plan.id} className="stack">
            <PricingCard plan={plan} />
            {plan.id !== 'free' && (
              <button type="button" onClick={() => requestUpgrade(plan.id)}>
                Request {plan.name}
              </button>
            )}
          </div>
        ))}
      </div>
      <button type="button" onClick={startPaddle}>Pay with Paddle</button>
      {message && <p>{message}</p>}
    </div>
  )
}
