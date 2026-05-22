import { useEffect, useMemo, useState } from 'react'
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
      <h1>Boundary Protection</h1>
      <Card title="Boundary Health Score" subtitle="Composite trust across channel boundaries.">
        <div className="health-score">{boundaryHealth}%</div>
      </Card>
      <section className="grid">
        {mapped.map((channel) => (
          <BoundaryCard key={channel.channel} {...channel} />
        ))}
      </section>
    </main>
  )
}
