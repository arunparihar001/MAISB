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
    apiRequest<DashboardData>(withApiKey('/v1/public/dashboard', key))
      .then(setData)
      .catch((err: Error) => setError(err.message))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <p>Loading dashboard...</p>

  return (
    <div className="stack">
      <h2>Dashboard</h2>
      <div className="grid">
        <MetricCard title="Plan" value={data.customer.plan} />
        <MetricCard title="Scans" value={data.usage.scan_count} />
        <MetricCard title="Remaining" value={data.usage.remaining} />
      </div>
      <UsageChart used={data.usage.scan_count} limit={data.usage.limit} />
    </div>
  )
}
