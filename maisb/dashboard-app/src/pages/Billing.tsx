import Badge from '../components/Badge'
import Card from '../components/Card'
import { getSelectedPlan } from '../lib/auth'

export default function Billing() {
  const plan = getSelectedPlan() || 'free'

  return (
    <main className="stack">
      <h1>Billing</h1>
      <Card title="Current plan">
        <Badge>{plan.toUpperCase()} active</Badge>
      </Card>
      <Card title="Pro and Certify">
        <p className="muted">Coming Soon / Request Invoice</p>
        <p className="muted">Online checkout is being configured. We do not currently collect card payments directly on this website. For Pro, Enterprise, or MAISB Certify, request an invoice or contact sales.</p>
      </Card>
    </main>
  )
}
