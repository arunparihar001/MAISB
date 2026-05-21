import { useEffect, useState } from 'react'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey, getUserEmail, maskSecret, setApiKey, setKeyId } from '../lib/auth'

type UsageData = { api_key_masked?: string }
type GenerateResponse = { created: boolean; key_id: string; api_key: string; email: string; warning: string }

export default function ApiKeys() {
  const [masked, setMasked] = useState(maskSecret(getApiKey()))
  const [rawKey, setRawKey] = useState('')
  const [warning, setWarning] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const email = getUserEmail()
  const hasKey = Boolean(getApiKey())

  useEffect(() => {
    const key = getApiKey()
    if (!key) return
    apiRequest<UsageData>(withApiKey('/v1/public/usage', key))
      .then((d) => setMasked(d.api_key_masked || maskSecret(key)))
      .catch(() => setMasked(maskSecret(key)))
  }, [])

  async function generateKey() {
    if (!email) {
      setError('Email not found. Please sign up and verify your email first.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<GenerateResponse>('/v1/profile/api-keys', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setApiKey(data.api_key)
      setKeyId(data.key_id)
      setRawKey(data.api_key)
      setMasked(maskSecret(data.api_key))
      setWarning(data.warning)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="stack">
      <h2>API Keys</h2>
      {rawKey ? (
        <div className="card">
          <h3>API key created</h3>
          <p><strong>Copy this key now — it will not be shown again.</strong></p>
          <pre style={{ background: '#f1f5f9', padding: '12px', borderRadius: '8px', overflowX: 'auto' }}>
            {rawKey}
          </pre>
          <p className="muted">{warning}</p>
        </div>
      ) : hasKey ? (
        <ApiKeyCard apiKeyMasked={masked} />
      ) : (
        <div className="card">
          <h3>Generate your API key</h3>
          <p>
            Your email has been verified. Click below to generate your first API key.
            The raw key is shown only once — copy it immediately.
          </p>
          {email && <p className="muted">Account: {email}</p>}
          <button onClick={generateKey} disabled={loading}>
            {loading ? 'Generating…' : 'Generate API key'}
          </button>
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {hasKey && !rawKey && (
        <p className="muted">
          Key rotation and revocation can be added when the backend exposes dedicated
          key-management endpoints.
        </p>
      )}
    </div>
  )
}

