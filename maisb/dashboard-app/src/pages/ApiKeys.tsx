import { useEffect, useState } from 'react'
import { apiGet } from '../lib/api'
import { getApiKey } from '../lib/auth'
import ApiKeyCard from '../components/ApiKeyCard'

export default function ApiKeys() {
  const [masked, setMasked] = useState('')
  useEffect(() => {
    const apiKey = getApiKey()
    if (!apiKey) return
    apiGet<{ api_key_masked: string }>('/v1/public/usage', { api_key: apiKey }).then((d) => setMasked(d.api_key_masked)).catch(() => undefined)
  }, [])
  return <main className="page"><h1>API Keys</h1><ApiKeyCard masked={masked} /></main>
}
