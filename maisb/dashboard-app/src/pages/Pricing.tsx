import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    copy: 'Sample data, core dashboard access, and API key generation.',
    features: ['Boundary scans', 'Single workspace', 'Sample data labels'],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'Request invoice',
    copy: 'Operational analytics, team controls, and higher scan volume.',
    features: ['Analytics', 'Team access', 'Priority traceability'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Request invoice',
    copy: 'Security governance, certification, and enterprise rollout support.',
    features: ['SSO-ready posture', 'Compliance reports', 'Dedicated support'],
  },
]

export default function Pricing() {
  return (
    <main className="public-shell narrow">
      <div className="page-head">
        <div>
          <p className="eyebrow">Pricing</p>
          <h1>Enterprise plans with clear boundaries.</h1>
          <p className="muted">Free starts now. Pro and Enterprise are invoice-based during rollout.</p>
        </div>
        <Link to="/signup"><Button>Begin onboarding</Button></Link>
      </div>

      <section className="grid">
        {plans.map((plan) => (
          <Card key={plan.id} title={plan.name} subtitle={plan.price} className={plan.id === 'enterprise' ? 'plan-highlight' : ''}>
            <p className="muted">{plan.copy}</p>
            <ul className="bullet-list">
              {plan.features.map((feature) => <li key={feature}>{feature}</li>)}
            </ul>
          </Card>
        ))}
      </section>

      <Card title="Commercial posture" subtitle="Security-first onboarding">
        <p className="muted">
          Online checkout is being configured. We do not currently collect card payments directly on this website. For Pro, Enterprise, or MAISB Certify, request an invoice or contact sales.
        </p>
      </Card>
    </main>
  )
}
