import { useEffect, useState } from 'react'
import UsageChart from '../components/UsageChart'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type UsageData = {
  scan_count: number
  limit: number
}

export default function Usage() {
  const [usage, setUsage] = useState<UsageData | null>(null)

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<UsageData>(withApiKey('/v1/public/usage', key)).then(setUsage)
  }, [])

  return (
    <div className="stack">
      <h2>Usage</h2>
      {usage ? <UsageChart used={usage.scan_count} limit={usage.limit} /> : <p>Loading usage...</p>}
    </div>
  )
}
