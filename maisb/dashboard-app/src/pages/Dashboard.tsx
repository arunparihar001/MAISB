import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import { getApiKey } from '../lib/auth'
import MetricCard from '../components/MetricCard'
import UsageChart from '../components/UsageChart'

export default function Dashboard() {
  const [usage, setUsage] = useState({ scan_count: 0, limit: 1000, plan: 'free' })
  useEffect(() => {
    const apiKey = getApiKey()
    if (!apiKey) return
    apiGet<{ usage: { scan_count: number; limit: number; plan: string } }>('/v1/public/dashboard', { api_key: apiKey })
      .then((d) => setUsage(d.usage))
      .catch(() => undefined)
  }, [])
  return <main className="page"><h1>Dashboard</h1><div className="grid"><MetricCard label="Plan" value={usage.plan} /><MetricCard label="Scans" value={usage.scan_count} /></div><UsageChart used={usage.scan_count} limit={usage.limit || 0} /></main>
}
