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

  const channelDescriptions: Record<string, string> = {
    'Clipboard': 'Content pasted from clipboard. Attackers can hide injection vectors in shared clipboard data.',
    'QR': 'QR codes scanned in-app. Malicious QR codes can point to pages with embedded system prompts.',
    'Notification': 'Push and system notifications. Third-party notification content can be copy-pasted into AI assistants.',
    'Deep Link': 'App deep links and universal links. URL parameters can carry instruction fragments and override intent.',
    'Share Intent': 'Android share intents and iOS share sheets. Shared content can carry hidden prompts.',
    'WebView': 'Content loaded in embedded browsers. Untrusted websites can inject JavaScript that modifies AI context.',
    'NFC': 'NFC tag data. Malicious NFC tags can carry instructions disguised as metadata.',
  }

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Boundary policy</p>
          <h1>Boundary Protection</h1>
          <p className="muted">Each channel is treated as an untrusted boundary before content reaches the LLM.</p>
        </div>
        <Badge>Sample data</Badge>
      </div>

      <Card title="Boundary Health Score" subtitle="Composite trust across channel boundaries.">
        <div className="health-score">{boundaryHealth}%</div>
        <p className="muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          A score above 80% indicates that most channel inputs are trustworthy. Scores below 60% suggest coordinated attack attempts or policy misconfigurations.
        </p>
      </Card>

      <section className="grid two-col">
        <Card title="Scanning posture" subtitle="Channels under continuous observation">
          <p className="muted">Clipboard, QR, NFC, notifications, webviews, and deep links are evaluated with consistent policy controls. Every channel boundary is scored independently and cross-linked for trace correlation.</p>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Badge>{REQUIRED_CHANNELS.length} channels protected</Badge>
            <Badge>{mapped.filter((c) => c.status === 'Active').length} active</Badge>
          </div>
        </Card>
        <Card title="Traceability" subtitle="Every decision is auditable">
          <p className="muted">Boundary events retain channel lineage, timestamps, risk scores, and decisions for downstream review. Traces show when multiple channels are coordinated in a single attack pattern.</p>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Badge>Audit-ready</Badge>
            <Badge>Cross-channel links</Badge>
          </div>
        </Card>
      </section>

      <section className="grid">
        {mapped.map((channel) => (
          <div key={channel.channel}>
            <BoundaryCard {...channel} />
            {channelDescriptions[channel.channel] && (
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem', paddingLeft: '0.5rem', borderLeft: '2px solid rgba(96, 165, 250, 0.2)' }}>
                {channelDescriptions[channel.channel]}
              </div>
            )}
          </div>
        ))}
      </section>

      <Card title="Policy enforcement" subtitle="How boundaries are applied">
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Risk-based decisions</p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>Each scan returns a risk_score (0.0-1.0). Your app decides: ALLOWED (low risk), REVIEW (medium risk), or BLOCKED (high risk).</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Metadata-only scoring</p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>MAISB scores channel metadata, patterns, and context—not raw content. Raw payloads are never stored.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Cross-channel correlation</p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>A single clipboard paste may be low-risk. But if the same content appears across QR, notification, and deep link channels in quick succession, trust degrades and risk rises.</p>
          </div>
        </div>
      </Card>
    </main>
  )
}
