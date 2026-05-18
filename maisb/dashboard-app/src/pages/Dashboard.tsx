import { useEffect, useState } from 'react'
import MetricCard from '../components/MetricCard'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type DashboardData = {
  customer: { email: string; plan: string; api_key_masked: string }
  usage: { scan_count: number; limit: number; remaining: number }
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<DashboardData>(withApiKey('/v1/public/dashboard', key)).then(setData).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load dashboard'))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <p className="muted">Loading dashboard...</p>

  return (
    <section className="stack">
      <div className="grid metrics">
        <MetricCard title="Plan" value={data.customer.plan.toUpperCase()} />
        <MetricCard title="Scans" value={data.usage.scan_count} subtitle="This month" />
        <MetricCard title="Remaining" value={data.usage.remaining} subtitle="Quota left" />
      </div>
      <UsageChart used={data.usage.scan_count} limit={data.usage.limit} />
    </section>
  )
}
