import { FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest } from '../lib/api'

type ResetPasswordResponse = {
  ok: true
  message: string
}

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const [token, setToken] = useState(searchParams.get('token') || '')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const data = await apiRequest<ResetPasswordResponse>('/v1/profile/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, password, confirm_password: confirmPassword }),
      })
      setMessage(data.message)
      setTimeout(() => navigate('/login', { replace: true }), 1400)
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
          <p className="eyebrow">Password recovery</p>
          <h1>Reset password</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Choose a new password and confirm it to complete the reset.
          </p>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
              Reset token
            </label>
            <input
              required
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste token from email"
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
              New password
            </label>
            <input
              required
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
              Confirm new password
            </label>
            <input
              required
              type="password"
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <Button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1rem' }}>
            {loading ? 'Resetting…' : 'Reset password'}
          </Button>

          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/login" style={{ fontSize: '0.9rem' }}>Back to login →</Link>
          </div>

          {message && <p className="notice">{message}</p>}
          {error && <p className="error">{error}</p>}
        </form>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Reset requirements" subtitle="Password rules">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>At least 8 characters</li>
              <li>Both password fields must match</li>
              <li>Tokens expire shortly after being issued</li>
            </ul>
          </Card>

          <Card title="After reset" subtitle="Next steps">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Once the reset completes, log back in with your new password and continue to your dashboard.
            </p>
            <Link to="/login">
              <Button variant="secondary">Go to login</Button>
            </Link>
          </Card>

          <Badge>🔒 Reset tokens can only be used once</Badge>
        </div>
      </div>
    </main>
  )
}
