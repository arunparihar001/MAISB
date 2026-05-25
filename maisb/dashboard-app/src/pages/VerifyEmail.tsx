import { FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiRequest } from '../lib/api'

type VerifyResponse = { verified: boolean; email?: string }

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const [token, setToken] = useState(searchParams.get('token') || '')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success'>('idle')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setStatus('loading')
    setMessage('')
    setError('')
    try {
      const data = await apiRequest<VerifyResponse>('/v1/profile/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token }),
      })
      setStatus('success')
      setMessage(data.email ? `${data.email} verified successfully.` : 'Email verified successfully.')
      setTimeout(() => navigate('/login'), 1400)
    } catch (err) {
      setStatus('idle')
      setError((err as Error).message)
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card glass-card" onSubmit={onSubmit}>
        <p className="eyebrow">Verification boundary</p>
        <h1>Verify Email</h1>
        <p className="muted">Paste your verification token to complete trusted access.</p>
        <input required value={token} onChange={(e) => setToken(e.target.value)} placeholder="Verification token" />
        <button type="submit" disabled={status === 'loading'}>{status === 'loading' ? 'Verifying…' : 'Verify token'}</button>
        <Link to="/login">Back to login</Link>
        {message && <p className="notice">{message}</p>}
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}
