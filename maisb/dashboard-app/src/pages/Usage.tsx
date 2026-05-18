import { useEffect, useState } from 'react'
import UsageChart from '../components/UsageChart'
import MetricCard from '../components/MetricCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type UsageData = { scan_count: number; limit: number; remaining?: number; plan?: string }

export default function Usage() {
  const [usage, setUsage] = useState<UsageData | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { const key = getApiKey(); if (!key) return; apiRequest<UsageData>(withApiKey('/v1/public/usage', key)).then(setUsage).catch((e) => setError((e as Error).message)) }, [])
  return <div className="stack"><h2>Usage + quota</h2>{error && <p className="error">{error}</p>}{usage ? <><div className="grid"><MetricCard title="Plan" value={usage.plan || 'free'} /><MetricCard title="Used" value={usage.scan_count} /><MetricCard title="Limit" value={usage.limit} /></div><UsageChart used={usage.scan_count} limit={usage.limit} /></> : <p>Loading usage...</p>}</div>
}
