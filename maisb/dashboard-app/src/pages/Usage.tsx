import { useEffect, useState } from 'react'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type UsageResponse = { scan_count: number; limit: number; remaining: number; plan: string }

export default function Usage() {
  const [usage, setUsage] = useState<UsageResponse | null>(null)

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<UsageResponse>(withApiKey('/v1/public/usage', key)).then(setUsage).catch(() => setUsage(null))
  }, [])

  if (!usage) return <p className="muted">Loading usage...</p>

  return (
    <section className="stack">
      <h1>Usage</h1>
      <UsageChart used={usage.scan_count} limit={usage.limit} />
      <p className="muted">Plan: {usage.plan} · Remaining scans: {usage.remaining}</p>
    </section>
  )
}
