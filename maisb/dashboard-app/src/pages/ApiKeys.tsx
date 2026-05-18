import { useEffect, useState } from 'react'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

interface UsageResponse {
  api_key_masked: string
  plan: string
  created: string
}

export default function ApiKeys() {
  const [usage, setUsage] = useState<UsageResponse | null>(null)

  useEffect(() => {
    const apiKey = getApiKey()
    apiRequest<UsageResponse>(withApiKey('/v1/public/usage', apiKey)).then(setUsage).catch(() => setUsage(null))
  }, [])

  return (
    <div className="page-grid">
      <ApiKeyCard keyMasked={usage?.api_key_masked || ''} />
      <div className="card">
        <h3>Key details</h3>
        <p>Plan: {usage?.plan || '-'}</p>
        <p>Created: {usage?.created || '-'}</p>
      </div>
    </div>
  )
}
