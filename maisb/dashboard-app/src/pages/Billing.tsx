import { useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { getSelectedPlan } from '../lib/auth'

export default function Billing() {
  const plan = getSelectedPlan() || 'free'
  const [tab, setTab] = useState<'summary' | 'plans' | 'support'>('summary')

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Billing</p>
          <h1>Billing</h1>
          <p className="muted">Invoice-based commercial rollout with clear status indicators.</p>
        </div>
        <Badge>{plan.toUpperCase()} active</Badge>
      </div>

      <Card
        title="Billing console"
        actions={
          <div className="tab-strip">
            {(['summary', 'plans', 'support'] as const).map((item) => (
              <button key={item} type="button" className={tab === item ? 'tab active' : 'tab'} onClick={() => setTab(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      >
        {tab === 'summary' && (
          <div className="grid two-col">
            <Card title="Current plan">
              <Badge>{plan.toUpperCase()} active</Badge>
              <p className="muted">Current entitlement state for this workspace.</p>
            </Card>
            <Card title="Invoice status">
              <p className="muted">Payments are manual during rollout. Support can issue an invoice for Pro, Enterprise, or Certify.</p>
            </Card>
          </div>
        )}

        {tab === 'plans' && (
          <Card title="Pro and Certify">
            <p className="muted">Online checkout is being configured. We do not currently collect card payments directly on this website. For Pro, Enterprise, or MAISB Certify, request an invoice or contact sales.</p>
          </Card>
        )}

        {tab === 'support' && (
          <Card title="Commercial support">
            <p className="muted">Request invoice</p>
            <Button variant="secondary">Contact sales</Button>
          </Card>
        )}
      </Card>
    </main>
  )
}
