import { useEffect, useMemo, useState } from 'react'
import Badge from '../components/Badge'
import BoundaryCard from '../components/BoundaryCard'
import Card from '../components/Card'
import { apiRequest } from '../lib/api'
import { REQUIRED_CHANNELS, normalizeChannelName } from '../lib/dashboard'

type Channel = { channel: string; events: number; blocked: number; trust_score: number }

export default function BoundaryProtection() {
  const [channels, setChannels] = useState<Channel[]>([])

  useEffect(() => {
    apiRequest<{ channels: Channel[] }>('/v1/dashboard/security/channel-reputation')
      .then((data) => setChannels(data.channels || []))
      .catch(() => setChannels([]))
  }, [])

  const mapped = useMemo(() => {
    const index = new Map<string, Channel>()
    channels.forEach((item) => index.set(normalizeChannelName(item.channel), item))
    return REQUIRED_CHANNELS.map((name) => {
      const found = index.get(name)
      return {
        channel: name,
        status: found ? 'Active' : 'Monitoring',
        scans: found?.events || 0,
        blocked: found?.blocked || 0,
        reputation: found?.trust_score ?? 0.86,
      }
    })
  }, [channels])

  const boundaryHealth = Math.round((mapped.reduce((sum, item) => sum + item.reputation, 0) / mapped.length) * 100)

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Boundary policy</p>
          <h1>Boundary Protection</h1>
          <p className="muted">Channel inputs are scored before they reach the model boundary.</p>
        </div>
        <Badge>Sample data</Badge>
      </div>
      <Card title="Boundary Health Score" subtitle="Composite trust across channel boundaries.">
        <div className="health-score">{boundaryHealth}%</div>
      </Card>
      <section className="grid">
        <Card title="Scanning posture" subtitle="Channels under continuous observation">
          <p className="muted">Clipboard, QR, NFC, notifications, webviews, and deep links are evaluated with consistent policy controls.</p>
        </Card>
        <Card title="Traceability" subtitle="Every decision is auditable">
          <p className="muted">Boundary events retain channel lineage, timestamps, and scored verdicts for downstream review.</p>
        </Card>
      </section>
      <section className="grid">
        {mapped.map((channel) => (
          <BoundaryCard key={channel.channel} {...channel} />
        ))}
      </section>
    </main>
  )
}
