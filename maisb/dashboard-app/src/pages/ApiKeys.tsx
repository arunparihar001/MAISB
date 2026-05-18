import { useEffect, useState } from 'react'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey, maskSecret } from '../lib/auth'

type UsageData = { api_key_masked?: string }

export default function ApiKeys() {
  const [masked, setMasked] = useState(maskSecret(getApiKey()))
  useEffect(() => { const key = getApiKey(); if (!key) return; apiRequest<UsageData>(withApiKey('/v1/public/usage', key)).then((d) => setMasked(d.api_key_masked || maskSecret(key))).catch(() => setMasked(maskSecret(key))) }, [])
  return <div className="stack"><h2>API Keys</h2><ApiKeyCard apiKeyMasked={masked} /><p className="muted">Key rotation/revocation can be added when the backend exposes dedicated key-management endpoints.</p></div>
}
