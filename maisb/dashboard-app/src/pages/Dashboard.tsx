import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import { getApiKey } from '../lib/auth'
import MetricCard from '../components/MetricCard'
import UsageChart from '../components/UsageChart'

export default function Dashboard() {
  const [usage, setUsage] = useState({ scan_count: 0, limit: 1000, plan: 'free', remaining: 1000 })
  const planLabel = typeof usage.plan === 'string' ? usage.plan.toUpperCase() : 'FREE'

  useEffect(() => {
    const apiKey = getApiKey()
    if (!apiKey) return
    apiGet<{ usage: { scan_count: number; limit: number; plan: string; remaining?: number } }>('/v1/public/dashboard', { api_key: apiKey })
      .then((d) => setUsage({
        scan_count: d.usage.scan_count,
        limit: d.usage.limit,
        plan: d.usage.plan,
        remaining: d.usage.remaining ?? Math.max(0, (d.usage.limit || 0) - d.usage.scan_count),
      }))
      .catch(() => undefined)
  }, [])

  return (
    <main className="page">
      <h1>Security Overview</h1>
      <p className="muted-text">Live posture for your protected mobile AI runtime.</p>
      <div className="grid">
        <MetricCard label="Plan" value={planLabel} />
        <MetricCard label="Scans Processed" value={usage.scan_count} />
        <MetricCard label="Remaining Quota" value={usage.remaining} />
      </div>
      <UsageChart used={usage.scan_count} limit={usage.limit || 0} />
    </main>
  )
}
