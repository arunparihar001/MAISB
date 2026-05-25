import { useEffect, useMemo, useState } from 'react'
import Badge from '../components/Badge'
import Card from '../components/Card'
import StatCard from '../components/StatCard'
import { apiRequest } from '../lib/api'

type DecisionResponse = { decisions: Record<string, number> }
type ReputationResponse = { channels: Array<{ channel: string; events: number; blocked: number; trust_score: number }> }
type KeysResponse = { api_keys: Array<{ key_id: string; status: string }> }

export default function Dashboard() {
  const [decisions, setDecisions] = useState<Record<string, number>>({ ALLOWED: 0, REVIEW: 0, BLOCKED: 0 })
  const [avgRisk, setAvgRisk] = useState(0)
  const [activeKeys, setActiveKeys] = useState(0)
  const [error, setError] = useState('')

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

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Enterprise overview</p>
          <h1>Overview</h1>
          <p className="muted">Sample data is shown until live signals are available.</p>
        </div>
        <Badge>Sample data</Badge>
      </div>
      <section className="grid">
        <StatCard label="Total Scans" value={total} />
        <StatCard label="Blocked" value={decisions.BLOCKED || 0} />
        <StatCard label="Reviewed" value={decisions.REVIEW || 0} />
        <StatCard label="Allowed" value={decisions.ALLOWED || 0} />
        <StatCard label="Avg Risk Score" value={avgRisk.toFixed(2)} />
        <StatCard label="Active API Keys" value={activeKeys} />
      </section>

      <section className="grid">
        <Card title="Boundary Protection Active" subtitle="Runtime channel boundary controls are enabled.">
          <p className="muted">Clipboard, deep links, notifications, QR, NFC, share intents, and webviews are evaluated with policy-aware scoring.</p>
        </Card>
        <Card title="Cross-Channel Trace Engine" subtitle="Trace context before the LLM acts.">
          <p className="muted">MAISB protects mobile AI agents before untrusted channel content reaches the LLM.</p>
        </Card>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  )
}
