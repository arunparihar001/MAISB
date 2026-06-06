import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import StatCard from '../components/StatCard'
import { apiRequest } from '../lib/api'
import { getSelectedPlan } from '../lib/auth'

type DecisionResponse = { decisions: Record<string, number> }
type ReputationResponse = { channels: Array<{ channel: string; events: number; blocked: number; trust_score: number }> }
type KeysResponse = { api_keys: Array<{ key_id: string; status: string }> }

export default function Dashboard() {
  const [decisions, setDecisions] = useState<Record<string, number>>({ ALLOWED: 0, REVIEW: 0, BLOCKED: 0 })
  const [avgRisk, setAvgRisk] = useState(0)
  const [activeKeys, setActiveKeys] = useState(0)
  const [error, setError] = useState('')
  const plan = getSelectedPlan() || 'free'

  useEffect(() => {
    Promise.all([
      apiRequest<DecisionResponse>('/v1/dashboard/analytics/decision-breakdown'),
      apiRequest<ReputationResponse>('/v1/dashboard/security/channel-reputation'),
      apiRequest<KeysResponse>('/v1/api-keys'),
    ])
      .then(([decisionData, channelData, keyData]) => {
        setDecisions(decisionData.decisions || { ALLOWED: 0, REVIEW: 0, BLOCKED: 0 })
        const channels = channelData.channels || []
        if (channels.length) {
          const derived = channels.reduce((sum, item) => sum + (1 - (item.trust_score || 0)), 0) / channels.length
          setAvgRisk(Number(derived.toFixed(2)))
        }
        setActiveKeys((keyData.api_keys || []).filter((item) => item.status !== 'revoked').length)
      })
      .catch((err) => setError((err as Error).message))
  }, [])

  const total = useMemo(
    () => Object.values(decisions).reduce((sum, value) => sum + value, 0),
    [decisions],
  )

  const hasScans = total > 0

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Enterprise overview</p>
          <h1>Dashboard</h1>
          <p className="muted">Real-time boundary protection status and security metrics.</p>
        </div>
        <Badge>{plan.toUpperCase()} · {hasScans ? 'Live' : 'Sample'} data</Badge>
      </div>

      {!hasScans && (
        <Card
          title="Getting started"
          subtitle="Send your first API scan"
          actions={<Badge>Step 1 of 3</Badge>}
        >
          <p className="muted" style={{ marginBottom: '1rem' }}>
            You haven't sent any scans yet. Start by sending a request to the <code style={{ background: 'rgba(96, 165, 250, 0.1)', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>/v1/scan</code> endpoint using your API key.
          </p>
          <div
            style={{
              background: 'rgba(96, 165, 250, 0.05)',
              border: '1px solid rgba(96, 165, 250, 0.15)',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '1rem',
              overflow: 'auto',
            }}
          >
            <code style={{ fontSize: '0.85rem', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
{`curl -X POST https://api.maisb.app/v1/scan \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{"channel":"clipboard","content_preview":"hello"}'`}
            </code>
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/docs/api">
              <Button variant="secondary">View API docs</Button>
            </Link>
            <a href="/api-keys">
              <Button variant="secondary">View API keys</Button>
            </a>
          </div>
        </Card>
      )}

      <section className="grid">
        <StatCard label="Total Scans" value={total} hint={hasScans ? 'All time' : 'Sample data'} />
        <StatCard label="Blocked" value={decisions.BLOCKED || 0} hint={`${((decisions.BLOCKED / (total || 1)) * 100).toFixed(0)}% of traffic`} />
        <StatCard label="Reviewed" value={decisions.REVIEW || 0} hint={`${((decisions.REVIEW / (total || 1)) * 100).toFixed(0)}% of traffic`} />
        <StatCard label="Allowed" value={decisions.ALLOWED || 0} hint={`${((decisions.ALLOWED / (total || 1)) * 100).toFixed(0)}% of traffic`} />
        <StatCard label="Avg Risk Score" value={avgRisk.toFixed(2)} hint="0.0 = safe, 1.0 = critical" />
        <StatCard label="Active API Keys" value={activeKeys} hint={`Ready to scan`} />
      </section>

      <section className="grid two-col">
        <Card title="Boundary Protection Active" subtitle="Runtime channel boundary controls are enabled.">
          <p className="muted">
            Clipboard, deep links, notifications, QR, NFC, share intents, and webviews are evaluated with policy-aware scoring. Every channel input is scored independently and cross-linked for attack pattern detection.
          </p>
          <div style={{ marginTop: '1rem' }}>
            <a href="/boundary-protection">
              <Button variant="secondary">View channels →</Button>
            </a>
          </div>
        </Card>

        <Card title="Cross-Channel Trace Engine" subtitle="Trace context before the LLM acts.">
          <p className="muted">
            MAISB traces mobile channel sequences to detect coordinated attacks. A single prompt injection may be low-risk. But when the same content appears across multiple channels in quick succession, our trace engine flags the pattern.
          </p>
          <div style={{ marginTop: '1rem' }}>
            <a href="/traces">
              <Button variant="secondary">View traces →</Button>
            </a>
          </div>
        </Card>

        <Card title="Security Events" subtitle="Recent boundary decisions and activity.">
          <p className="muted">
            Every boundary decision is logged with timestamp, channel, risk score, and trace ID. Review blocked and flagged events to understand your security posture.
          </p>
          <div style={{ marginTop: '1rem' }}>
            <a href="/security-events">
              <Button variant="secondary">View events →</Button>
            </a>
          </div>
        </Card>

        <Card title="Workspace Health" subtitle="Team, API keys, and entitlements.">
          <div style={{ display: 'grid', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="muted">Plan</span>
              <strong>{plan.charAt(0).toUpperCase() + plan.slice(1)}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="muted">Active Keys</span>
              <strong>{activeKeys}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="muted">Data Retention</span>
              <strong>30 days</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="muted">Status</span>
              <Badge>Online</Badge>
            </div>
          </div>
        </Card>
      </section>

      {!hasScans && (
        <Card title="What's next?" subtitle="Your onboarding path">
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>1</span>
              <div>
                <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Send your first scan</p>
                <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>POST to /v1/scan with your API key</p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>2</span>
              <div>
                <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Review security events</p>
                <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>View decisions, risk scores, and traces</p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>3</span>
              <div>
                <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Invite your team</p>
                <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Add Analysts or Viewers to your workspace</p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {error && <p className="error">{error}</p>}
    </main>
  )
}
