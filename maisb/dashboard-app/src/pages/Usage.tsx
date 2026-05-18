import { useEffect, useState } from 'react'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

interface UsageData {
  scan_count: number
  limit: number
  remaining: number
}

export default function Usage() {
  const [usage, setUsage] = useState<UsageData | null>(null)

  useEffect(() => {
    const apiKey = getApiKey()
    apiRequest<UsageData>(withApiKey('/v1/public/usage', apiKey)).then(setUsage).catch(() => setUsage(null))
  }, [])

  return usage ? <UsageChart used={usage.scan_count} limit={usage.limit} /> : <p className="muted">Loading usage…</p>
}
