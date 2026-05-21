import { useEffect, useState } from 'react'
import MetricCard from '../components/MetricCard'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type DashboardData = { customer?: { email?: string; plan?: string; api_key_masked?: string }; usage?: { scan_count?: number; limit?: number; remaining?: number } }

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { const key = getApiKey(); if (!key) return; apiRequest<DashboardData>(withApiKey('/v1/public/dashboard', key)).then(setData).catch((e) => setError((e as Error).message)) }, [])
  if (error) return <div className="stack"><p className="error">{error}</p></div>
  if (!data) return <div className="stack"><div className="card"><p>Loading dashboard...</p></div></div>
  const usage = data.usage || {}
  return <div className="stack"><h2>Customer overview</h2><div className="grid"><MetricCard title="Plan" value={data.customer?.plan || 'free'} /><MetricCard title="Scans" value={usage.scan_count || 0} /><MetricCard title="Remaining" value={usage.remaining ?? Math.max(0, (usage.limit || 1000) - (usage.scan_count || 0))} /></div><UsageChart used={usage.scan_count || 0} limit={usage.limit || 1000} /><div className="card"><h3>Verified profile</h3><p>Email: <code>{data.customer?.email || 'Not set'}</code></p><p>API key: <code>{data.customer?.api_key_masked || 'Not available'}</code></p></div><div className="card"><h3>Quick links</h3><p><a href="https://api.maisb.app/docs" target="_blank">API Docs</a> · <a href="/certify">Start Certify</a> · <a href="/billing">Upgrade plan</a></p></div></div>
}
