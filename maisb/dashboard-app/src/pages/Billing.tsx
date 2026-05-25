import { useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { getSelectedPlan } from '../lib/auth'

export default function Billing() {
  const plan = getSelectedPlan() || 'free'
  const [tab, setTab] = useState<'summary' | 'plans' | 'usage'>('summary')

  const planFeatures = {
    free: ['Boundary scans', 'Dashboard access', 'API key management', 'Sample data labels'],
    pro: ['All Free features', 'Team members', 'Advanced analytics', 'Compliance reports', 'Priority support'],
    enterprise: ['All Pro features', 'SSO integration', 'Custom audit trails', 'Dedicated support', 'SLA guarantee'],
  }

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Billing</p>
          <h1>Billing & Plans</h1>
          <p className="muted">Transparent pricing with invoice-based commercial rollout. Pro, Certify, and Enterprise available by request.</p>
        </div>
        <Badge>{plan.toUpperCase()} active</Badge>
      </div>

      <Card
        title="Billing console"
        actions={
          <div className="tab-strip">
            {(['summary', 'plans', 'usage'] as const).map((item) => (
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
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 500, textTransform: 'uppercase' }}>{plan}</span>
                <Badge>Active</Badge>
              </div>
              <p className="muted">Your workspace is currently on the {plan} plan. Start free with sample data. Upgrade to Pro or Enterprise as you scale.</p>
              {plan === 'free' && (
                <div style={{ marginTop: '1rem' }}>
                  <a href="mailto:sales@maisb.app"><Button variant="secondary">Discuss Pro pricing</Button></a>
                </div>
              )}
            </Card>

            <Card title="Invoice & billing">
              <p className="muted">MAISB uses invoice-based billing during early access. No card payments are collected directly on this website.</p>
              <p className="muted" style={{ marginTop: '0.75rem' }}>
                <strong>Ready to upgrade?</strong><br/>Contact <a href="mailto:sales@maisb.app">sales@maisb.app</a> to request a Pro or Enterprise invoice.
              </p>
            </Card>

            <Card title="Usage" subtitle="Scans and API quota">
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="muted">Current period</span>
                  <strong>This month</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="muted">Total scans</span>
                  <strong>2,847</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="muted">API keys active</span>
                  <strong>2</strong>
                </div>
              </div>
            </Card>

            <Card title="Free tier limits" subtitle="Development-grade quotas">
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div>
                  <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>Rate limit</p>
                  <strong>100 scans/min</strong>
                </div>
                <div>
                  <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>Workspace members</p>
                  <strong>1 member</strong>
                </div>
                <div>
                  <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>Retention</p>
                  <strong>30 days</strong>
                </div>
              </div>
            </Card>
          </div>
        )}

        {tab === 'plans' && (
          <div className="grid">
            {Object.entries(planFeatures).map(([planName, features]) => (
              <Card
                key={planName}
                title={planName.charAt(0).toUpperCase() + planName.slice(1)}
                className={planName === plan ? 'plan-highlight' : ''}
              >
                <ul className="bullet-list" style={{ margin: 0 }}>
                  {features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
                <div style={{ marginTop: '1.5rem' }}>
                  {planName === 'free' ? (
                    <p className="muted" style={{ fontSize: '0.9rem' }}>
                      {plan === 'free' ? 'Current plan' : 'Downgrade available'}
                    </p>
                  ) : (
                    <a href="mailto:sales@maisb.app"><Button variant="secondary">Request invoice</Button></a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}

        {tab === 'usage' && (
          <div className="grid">
            <Card title="Current month" subtitle="May 2026">
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Boundary scans</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                    <strong style={{ fontSize: '1.5rem' }}>2,847</strong>
                    <span className="muted" style={{ fontSize: '0.85rem' }}>Free tier limit: Unlimited</span>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="API quota" subtitle="Current rate limits">
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div>
                  <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.35rem' }}>Requests per minute</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="bar-track" style={{ flex: 1 }}>
                      <div className="bar-fill" style={{ width: '35%' }} />
                    </div>
                    <span style={{ fontSize: '0.85rem', whiteSpace: 'nowrap' }}>35 / 100</span>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Storage" subtitle="Data retention policy">
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div>
                  <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Free tier</p>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>30-day retention. Metadata only—raw payloads never stored.</p>
                </div>
                <div style={{ paddingTop: '0.75rem', borderTop: '1px solid rgba(148, 163, 184, 0.12)' }}>
                  <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Pro tier</p>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>90-day retention. Extended analytics and compliance exports.</p>
                </div>
              </div>
            </Card>

            <Card title="Overages" subtitle="What happens when you exceed limits">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                Free tier: Requests exceeding the rate limit are queued for up to 60 seconds, then rejected with HTTP 429. Contact sales to move to Pro for production workloads.
              </p>
            </Card>
          </div>
        )}
      </Card>

      {plan === 'free' && (
        <Card title="Ready to scale?" subtitle="Move to production with Pro or Enterprise">
          <p className="muted">
            MAISB Free tier is designed for evaluation and development. When you're ready to deploy to production with live AI agent traffic, Pro and Enterprise plans include higher quotas, team access, and advanced analytics.
          </p>
          <div style={{ marginTop: '1rem' }}>
            <a href="mailto:sales@maisb.app"><Button>Contact sales</Button></a>
          </div>
        </Card>
      )}
    </main>
  )
}
