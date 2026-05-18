import { useEffect, useState } from 'react'
import MetricCard from '../components/MetricCard'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

interface DashboardResponse {
  customer: { email: string; plan: string; api_key_masked: string }
  usage: { scan_count: number; limit: number; remaining: number }
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const apiKey = getApiKey()
    apiRequest<DashboardResponse>(withApiKey('/v1/public/dashboard', apiKey))
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load dashboard'))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <p className="muted">Loading dashboard…</p>

  return (
    <div className="page-grid">
      <MetricCard label="Plan" value={data.customer.plan} />
      <MetricCard label="Scans" value={data.usage.scan_count} />
      <MetricCard label="Remaining" value={data.usage.remaining} />
      <MetricCard label="Customer" value={data.customer.email} />
      <UsageChart used={data.usage.scan_count} limit={data.usage.limit} />
    </div>
  )
}
