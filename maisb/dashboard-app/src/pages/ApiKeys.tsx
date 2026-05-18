import { useEffect, useState } from 'react'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey } from '../lib/auth'

type UsageData = {
  api_key_masked: string
}

export default function ApiKeys() {
  const [masked, setMasked] = useState('')

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<UsageData>(withApiKey('/v1/public/usage', key)).then((data) => setMasked(data.api_key_masked))
  }, [])

  return (
    <div className="stack">
      <h2>API Keys</h2>
      <ApiKeyCard apiKeyMasked={masked} />
    </div>
  )
}
