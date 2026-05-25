import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
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
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <p className="eyebrow">Step 2 of 3</p>
        <h1>Select your plan</h1>
        <p className="muted" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Start with Free and upgrade anytime. Pro, Certify, and Enterprise plans are invoice-based during our rollout.
        </p>
      </div>

      <section className="grid two-col" style={{ marginBottom: '2rem' }}>
        {plans.map((plan) => (
          <PlanCard
            key={plan.code}
            name={plan.name}
            code={plan.code}
            price={plan.code === 'free' ? '$0/month' : 'Custom pricing'}
            features={
              plan.code === 'free'
                ? ['Boundary scanning', 'API key generation', 'Core dashboard', 'Security events', 'Team invitations']
                : plan.code === 'pro'
                  ? ['Everything in Free', 'Advanced analytics', 'Team collaboration', 'Compliance reports', 'Priority support']
                  : ['Everything in Pro', 'Runtime assessment', 'Certify badge', 'Enterprise workflows', 'Dedicated support']
            }
            comingSoon={plan.coming_soon}
            onSelect={() => selectPlan(plan)}
            actionLabel={
              loadingCode === plan.code ? 'Working…' : plan.code === 'free' ? 'Start Free' : 'Request Invoice'
            }
          />
        ))}
      </section>

      <section className="grid two-col" style={{ marginBottom: '2rem' }}>
        <Card title="Free plan includes" subtitle="Start scanning immediately">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>Unlimited boundary scans via /v1/scan</li>
            <li>Dashboard with sample data</li>
            <li>API key generation and rotation</li>
            <li>Security event logging (30 days)</li>
            <li>Single team member</li>
            <li>Development-grade rate limits</li>
          </ul>
        </Card>

        <Card title="When to upgrade" subtitle="Pro and Enterprise planning">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>Moving to production (Pro)</li>
            <li>Adding team members (Pro)</li>
            <li>Longer retention needed (Pro+)</li>
            <li>Enterprise governance (Enterprise)</li>
            <li>Runtime certification (Certify)</li>
            <li>Custom integrations (Enterprise)</li>
          </ul>
        </Card>
      </section>

      <Card title="Commercial posture" subtitle="How we bill">
        <p className="muted" style={{ marginBottom: '1rem' }}>
          Free tier is available immediately and lasts as long as you need to evaluate MAISB. Pro, Certify, and Enterprise plans are invoice-based. We do not currently collect card payments directly on this website.
        </p>
        <p className="muted">
          <strong>Ready for production?</strong> Contact <a href="mailto:sales@maisb.app">sales@maisb.app</a> to discuss Pro or Enterprise pricing.
        </p>
      </Card>

      {message && <p className="notice">{message}</p>}
      {error && <p className="error">{error}</p>}

      <div style={{ textAlign: 'center', marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid rgba(148, 163, 184, 0.12)' }}>
        <Badge>You're almost done! Generate your API key in the next step.</Badge>
      </div>
    </main>
  )
}
