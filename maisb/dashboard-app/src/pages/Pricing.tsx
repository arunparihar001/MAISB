import { Link } from 'react-router-dom'
import Card from '../components/Card'

const plans = [
  { id: 'free', name: 'Free', price: '$0', copy: 'Developer access with basic dashboard and API key support.' },
  { id: 'pro', name: 'Pro', price: 'Request Invoice', copy: 'Expanded quotas and commercial onboarding. Coming soon.' },
  { id: 'certify', name: 'Certify', price: 'Request Invoice', copy: 'MAISB certification workflow and reporting. Coming soon.' },
]

export default function Pricing() {
  return (
    <main className="public-shell narrow">
      <h1>Pricing</h1>
      <p className="muted">Select Free to start now. Pro and Certify are invoice-based during rollout.</p>
      <section className="grid">
        {plans.map((plan) => (
          <Card key={plan.id} title={plan.name} subtitle={plan.price}>
            <p className="muted">{plan.copy}</p>
          </Card>
        ))}
      </section>
      <p className="muted">
        Online checkout is being configured. We do not currently collect card payments directly on this website. For Pro, Enterprise, or MAISB Certify, request an invoice or contact sales.
      </p>
      <Link to="/signup">Create account</Link>
    </main>
  )
}
