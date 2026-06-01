import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest } from '../lib/api'

type ForgotPasswordResponse = {
  ok: true
  message: string
}

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const data = await apiRequest<ForgotPasswordResponse>('/v1/profile/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setMessage(data.message)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="onboarding-page">
      <div className="grid two-col" style={{ alignItems: 'start', gap: '2rem' }}>
        <form className="glass-card" style={{ padding: '2rem' }} onSubmit={onSubmit}>
          <p className="eyebrow">Account recovery</p>
          <h1>Forgot password?</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Enter your email address and we&apos;ll send reset instructions if the account exists.
          </p>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
              Email address
            </label>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </div>

          <Button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1rem' }}>
            {loading ? 'Sending…' : 'Send reset instructions'}
          </Button>

          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/login" style={{ fontSize: '0.9rem' }}>Back to login →</Link>
          </div>

          {message && <p className="notice">{message}</p>}
          {error && <p className="error">{error}</p>}
        </form>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Security note" subtitle="Why this is safe">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>We never reveal whether an email exists</li>
              <li>Reset links expire after a short window</li>
              <li>Tokens can only be used once</li>
            </ul>
          </Card>

          <Card title="Need help?" subtitle="Contact support">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              If you are unable to access your email inbox, contact support and we can help verify your account.
            </p>
            <a href="mailto:support@maisb.app">
              <Button variant="secondary">Email support</Button>
            </a>
          </Card>

          <Badge>🔒 Password reset requests are handled securely</Badge>
        </div>
      </div>
    </main>
  )
}
