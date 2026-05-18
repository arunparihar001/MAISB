import { useEffect, useState } from 'react'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type UsageData = { api_key_masked: string; plan: string; created?: string }

export default function ApiKeys() {
  const [data, setData] = useState<UsageData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<UsageData>(withApiKey('/v1/public/usage', key)).then(setData).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load key metadata'))
  }, [])

  return (
    <section className="stack">
      <h1>API Keys</h1>
      {error ? <p className="error">{error}</p> : null}
      {data ? <ApiKeyCard maskedKey={data.api_key_masked} plan={data.plan} created={data.created} /> : <p className="muted">Loading key metadata...</p>}
      <p className="muted">For security, raw keys are shown once at signup only.</p>
    </section>
  )
}
