import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/Card'
import PlanCard from '../components/PlanCard'
import { apiRequest } from '../lib/api'
import { setSelectedPlan } from '../lib/auth'

type Plan = { code: string; name: string; coming_soon?: boolean; request_invoice?: boolean }
type PlansResponse = { plans: Plan[] }

const fallbackPlans: Plan[] = [
  { code: 'free', name: 'Free', coming_soon: false },
  { code: 'pro', name: 'Pro', coming_soon: true, request_invoice: true },
  { code: 'certify', name: 'Certify', coming_soon: true, request_invoice: true },
]

export default function SelectPlan() {
  const [plans, setPlans] = useState<Plan[]>(fallbackPlans)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loadingCode, setLoadingCode] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    apiRequest<PlansResponse>('/v1/plans')
      .then((data) => {
        if (Array.isArray(data.plans) && data.plans.length) setPlans(data.plans)
      })
      .catch(() => undefined)
  }, [])

  async function selectPlan(plan: Plan) {
    setLoadingCode(plan.code)
    setError('')
    setMessage('')
    try {
      const result = await apiRequest<{ selected?: boolean; plan: string; message?: string; coming_soon?: boolean }>('/v1/plans/select', {
        method: 'POST',
        body: JSON.stringify({ plan: plan.code }),
      })

      if (result.selected && result.plan === 'free') {
        setSelectedPlan('free')
        navigate('/api-keys', { replace: true })
        return
      }

      setMessage(result.message || 'Coming soon. Request invoice from sales@maisb.app')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoadingCode('')
    }
  }

  return (
    <main className="onboarding-page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Plan selection</p>
          <h1>Select your plan</h1>
          <p className="muted">Free is active today. Pro, Enterprise, and Certify are invoice-based during rollout.</p>
        </div>
      </div>
      <section className="grid">
        {plans.map((plan) => (
          <PlanCard
            key={plan.code}
            name={plan.name}
            code={plan.code}
            price={plan.code === 'free' ? '$0' : 'Request Invoice'}
            features={plan.code === 'free' ? ['Start immediately', 'API key generation', 'Core dashboard access'] : ['Coming soon access', 'Request invoice workflow']}
            comingSoon={plan.coming_soon}
            onSelect={() => selectPlan(plan)}
            actionLabel={loadingCode === plan.code ? 'Working…' : plan.code === 'free' ? 'Start Free' : 'Coming Soon / Request Invoice'}
          />
        ))}
      </section>
      <Card title="Commercial posture">
        <p className="muted">Online checkout is being configured. We do not currently collect card payments directly on this website. For Pro, Enterprise, or MAISB Certify, request an invoice or contact sales.</p>
      </Card>
      {message && <p className="notice">{message}</p>}
      {error && <p className="error">{error}</p>}
    </main>
  )
}
