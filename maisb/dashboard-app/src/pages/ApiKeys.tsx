import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ApiKeyCard from '../components/ApiKeyCard'
import { apiRequest, withApiKey } from '../lib/api'
import { getApiKey, maskSecret, setApiKey } from '../lib/auth'

type UsageData = { api_key_masked?: string; email?: string }
type ProfileStatus = { email: string; status: string; email_verified: boolean; has_api_key: boolean; api_key_masked?: string }
type ApiKeyCreateResponse = { created: boolean; api_key?: string; api_key_masked?: string; message?: string; warning?: string }

export default function ApiKeys() {
  const navigate = useNavigate()
  const storedKey = getApiKey()
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<ProfileStatus | null>(null)
  const [rawKey, setRawKey] = useState('')
  const [masked, setMasked] = useState(maskSecret(getApiKey()))
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!storedKey) return
    apiRequest<UsageData>(withApiKey('/v1/public/usage', storedKey))
      .then((d) => setMasked(d.api_key_masked || maskSecret(storedKey)))
      .catch(() => setMasked(maskSecret(storedKey)))
  }, [storedKey])

  async function checkStatus(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await apiRequest<ProfileStatus>(`/v1/profile/status?email=${encodeURIComponent(email.trim())}`)
      setStatus(data)
      setMasked(data.api_key_masked || 'Not available')
    } catch (err) {
      setStatus(null)
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function createKey() {
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const data = await apiRequest<ApiKeyCreateResponse>('/v1/profile/api-keys', { method: 'POST', body: JSON.stringify({ email: email.trim() }) })
      setRawKey(data.api_key || '')
      setMasked(data.api_key_masked || 'Not available')
      if (data.api_key) {
        setApiKey(data.api_key)
        setMessage(data.warning || 'Store this raw key now. It is shown once.')
      } else {
        setMessage(data.message || 'API key already exists. Only masked key is available.')
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="stack">
      <h2>API keys</h2>
      <div className="card">
        <ApiKeyCard apiKeyMasked={masked} />
        {rawKey && <p className="notice">Raw API key (shown once): <code>{rawKey}</code></p>}
        {!storedKey && (
          <form onSubmit={checkStatus} className="form-grid">
            <input required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Verified email" />
            <button type="submit" disabled={loading}>{loading ? 'Checking…' : 'Check profile status'}</button>
          </form>
        )}
        {status && (
          <div className="card">
            <p>Status: <b>{status.status}</b></p>
            <p>Email verified: {status.email_verified ? 'Yes' : 'No'}</p>
            <p>Has API key: {status.has_api_key ? 'Yes' : 'No'}</p>
            <button type="button" onClick={createKey} disabled={!status.email_verified || loading}>{status.has_api_key ? 'Refresh masked key' : 'Generate API key'}</button>
          </div>
        )}
        {storedKey && <button type="button" onClick={() => navigate('/dashboard')}>Open dashboard</button>}
        {message && <p className="notice">{message}</p>}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  )
}
