import { useState } from 'react'
import { apiRequest } from '../lib/api'
import { getStoredEmail, setApiKey, maskSecret } from '../lib/auth'

type GenerateKeyResponse = { key_id: string; raw_key: string; email: string; warning?: string }

export default function ApiKeys() {
  const [rawKey, setRawKey] = useState('')
  const [visible, setVisible] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const email = getStoredEmail()

  async function generateKey() {
    if (!email) { setError('Log in first so we know which profile to attach the key to.'); return }
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<GenerateKeyResponse>('/v1/profile/api-keys', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setRawKey(data.raw_key)
      setApiKey(data.raw_key)
      setVisible(true)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function copyKey() {
    if (!rawKey) return
    await navigator.clipboard.writeText(rawKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="stack">
      <h2>API Keys</h2>
      {rawKey ? (
        <div className="card">
          <h3>New API key generated</h3>
          <p className="muted">
            ⚠ Copy this key now. It will <b>not</b> be shown again.
          </p>
          <div style={{ display: 'flex', gap: '.6rem', alignItems: 'center', flexWrap: 'wrap', margin: '.6rem 0' }}>
            <code style={{ background: '#f1f5f9', padding: '.5rem .75rem', borderRadius: 8, flex: 1, wordBreak: 'break-all' }}>
              {visible ? rawKey : maskSecret(rawKey)}
            </code>
            <button className="secondary" onClick={() => setVisible((v) => !v)} style={{ whiteSpace: 'nowrap' }}>
              {visible ? 'Hide' : 'Show'}
            </button>
            <button onClick={copyKey} style={{ whiteSpace: 'nowrap' }}>
              {copied ? 'Copied ✓' : 'Copy'}
            </button>
          </div>
          <p className="muted">Store this key securely. Do not commit it to GitHub, screenshots, or reports.</p>
        </div>
      ) : (
        <div className="card">
          <h3>Generate API key</h3>
          <p className="muted">A new key will be created for <b>{email || 'your account'}</b>. The raw key is shown once.</p>
          <button onClick={generateKey} disabled={loading}>{loading ? 'Generating…' : 'Generate API key'}</button>
          {error && <p className="error">{error}</p>}
        </div>
      )}
      <p className="muted">Your key is stored in this browser's localStorage and injected as a Bearer token on all API requests.</p>
    </div>
  )
}

