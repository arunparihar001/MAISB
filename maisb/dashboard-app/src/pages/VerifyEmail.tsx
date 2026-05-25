import { FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
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

  if (status === 'success') {
    return (
      <main className="onboarding-page">
        <div className="grid two-col" style={{ alignItems: 'center' }}>
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
            <p className="eyebrow">Verification complete</p>
            <h1>✓ Email verified</h1>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              {message}
            </p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Redirecting to login...
            </p>
          </div>
          <Card title="What's next?" subtitle="Your onboarding path">
            <ol className="bullet-list" style={{ margin: 0 }}>
              <li>You're currently here: Email verified ✓</li>
              <li>Log in to your account</li>
              <li>Select your plan (Free recommended)</li>
              <li>Generate your first API key</li>
              <li>Start scanning with /v1/scan</li>
            </ol>
          </Card>
        </div>
      </main>
    )
  }

  return (
    <main className="onboarding-page">
      <div className="grid two-col" style={{ alignItems: 'start', gap: '2rem' }}>
        <form className="glass-card" style={{ padding: '2rem' }} onSubmit={onSubmit}>
          <p className="eyebrow">Verification boundary</p>
          <h1>Verify email</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Check your inbox for the verification token we sent. Paste it below to activate your workspace.
          </p>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
              Verification token
            </label>
            <input
              required
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste token from email"
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <Button type="submit" disabled={status === 'loading'}>
              {status === 'loading' ? 'Verifying…' : 'Verify token'}
            </Button>
          </div>

          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/login" style={{ fontSize: '0.9rem' }}>Back to login →</Link>
          </div>

          {message && <p className="notice">{message}</p>}
          {error && <p className="error">{error}</p>}
        </form>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Email verification" subtitle="Why it matters">
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Verification confirms you own the email address and protects your workspace from unauthorized access.
            </p>
          </Card>

          <Card title="Can't find the token?" subtitle="We can help">
            <ul className="bullet-list" style={{ margin: 0, fontSize: '0.9rem' }}>
              <li>Check your spam/junk folder</li>
              <li>Allow emails from support@maisb.app</li>
              <li>Wait a few minutes if it's delayed</li>
              <li>Contact support@maisb.app for help</li>
            </ul>
          </Card>

          <Card title="Security note" subtitle="Keeping you safe">
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Tokens expire after 24 hours. If yours has expired, you'll need to request a new one from the login page.
            </p>
          </Card>

          <Badge>
            🔒 Your workspace is protected until verification is complete
          </Badge>
        </div>
      </div>
    </main>
  )
}
