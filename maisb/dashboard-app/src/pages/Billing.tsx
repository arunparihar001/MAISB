import { useEffect, useState } from 'react'
import PricingCard, { Plan } from '../components/PricingCard'
import { apiRequest } from '../lib/api'

const fallbackPlans: Plan[] = [
  { id: 'free', name: 'Free Developer', price: '$0/month', features: ['Starter API key', 'Limited monthly scans', 'Basic usage dashboard', 'Android SDK testing'] },
  { id: 'pro', name: 'Pro', price: 'Invoice', features: ['Higher quota', 'Commercial use', 'Usage dashboard', 'Email support'], cta: 'Request Pro' },
  { id: 'enterprise', name: 'Enterprise', price: 'Custom', features: ['Custom quota', 'SOC workflow', 'Audit/export', 'Tenant policy controls'], cta: 'Request quote' },
  { id: 'certify', name: 'MAISB Certify', price: 'Assessment', features: ['PDF report', 'Badge SVG', 'Benchmark-style result'], cta: 'Request Certify' },
]

type PlansResponse = { plans: Plan[] }

export default function Billing() {
  const [plans, setPlans] = useState<Plan[]>(fallbackPlans)
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')
  useEffect(() => {
    apiRequest<PlansResponse>('/v1/public/plans')
      .then((d) => { if (d.plans?.length) setPlans(d.plans) })
      .catch(() => undefined)
  }, [])

  async function requestUpgrade(plan: string) {
    setMessage('')
    if (!email.trim()) { setMessage('Billing email is required'); return }
    try {
      const response = await apiRequest<{ request_id: string; status: string }>(
        '/v1/billing/upgrade-request',
        { method: 'POST', body: JSON.stringify({ email, company, plan, provider: 'manual_invoice' }) },
      )
      setMessage(`Upgrade request submitted: ${response.request_id}. Access changes after billing confirmation.`)
    } catch (err) { setMessage((err as Error).message) }
  }

  return (
    <div className="stack">
      <h2>Billing</h2>
      <div className="card">
        <p>
          Online checkout is being configured. For Pro, Enterprise, or MAISB Certify,
          please request an invoice or contact{' '}
          <a href="mailto:sales@maisb.app">sales@maisb.app</a>.
          Access changes only after billing approval. We do not currently collect
          card payments directly on this website.
        </p>
      </div>
      <div className="form-grid">
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Billing email" type="email" />
        <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company (optional)" />
      </div>
      <div className="grid">
        {plans.map((plan) => (
          <div key={plan.id} className="stack compact">
            <PricingCard plan={plan} />
            {plan.id === 'pro' && (
              <button onClick={() => requestUpgrade('pro')}>Request Pro invoice</button>
            )}
            {plan.id === 'enterprise' && (
              <button onClick={() => requestUpgrade('enterprise')}>Request Enterprise quote</button>
            )}
            {plan.id === 'certify' && (
              <button onClick={() => requestUpgrade('certify')}>Request Certify assessment</button>
            )}
          </div>
        ))}
      </div>
      {message && <p className="notice">{message}</p>}
    </div>
  )
}

