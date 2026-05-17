import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../lib/api'
import { createPaddleCheckout } from '../lib/paddle'

export default function Billing() {
  const [email, setEmail] = useState('')
  const [note, setNote] = useState('')
  const [plans, setPlans] = useState<Array<{ name: string; id: string }>>([])
  useEffect(() => { apiGet<{ plans: Array<{ name: string; id: string }> }>('/v1/public/plans').then((d) => setPlans(d.plans)).catch(() => undefined) }, [])
  const requestUpgrade = async (plan: string) => {
    await apiPost('/v1/billing/upgrade-request', { email, plan, provider: 'paddle' })
    setNote(`Upgrade request submitted for ${plan}.`)
  }
  const startCheckout = async (plan: 'pro' | 'certify') => {
    await createPaddleCheckout(email, plan)
    setNote(`Paddle checkout session created for ${plan}.`) 
  }
  return <main className="page"><h1>Billing</h1><p>Paddle-ready plans and upgrade requests.</p><input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Billing email" /><div className="grid">{plans.map((p) => <button key={p.id} onClick={() => requestUpgrade(p.id)}>{p.name}</button>)}</div><button onClick={() => startCheckout('pro')}>Start Pro Checkout</button><button onClick={() => startCheckout('certify')}>Start Certify Checkout</button><p>{note}</p></main>
}
