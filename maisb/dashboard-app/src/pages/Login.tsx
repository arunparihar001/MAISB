import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest } from '../lib/api'
import { clearSelectedPlan, setApiKeyExists, setSessionToken, setStoredEmail, setStoredProfile } from '../lib/auth'

type LoginResponse = {
  session_token: string
  profile: {
    id: string
    name?: string
    email: string
    company?: string
    use_case?: string
    verified: boolean
    plan?: string
  }
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const rawHash = window.location.hash.replace(/^#/, '')
    if (!rawHash) return

    try {
      const params = new URLSearchParams(rawHash)
      const sessionToken = params.get('session_token') || ''
      const profileRaw = params.get('profile') || ''
      if (!sessionToken) return

      const profile = profileRaw ? (JSON.parse(profileRaw) as LoginResponse['profile']) : null
      setSessionToken(sessionToken)
      if (profileRaw) {
        setStoredProfile(profile as LoginResponse['profile'])
        setStoredEmail((profile as LoginResponse['profile']).email)
      }
      clearSelectedPlan()
      setApiKeyExists(false)
      window.history.replaceState({}, document.title, window.location.pathname + window.location.search)
      navigate('/select-plan', { replace: true })
    } catch (error) {
      console.error('Failed to process OAuth login fragment', error)
      window.history.replaceState({}, document.title, window.location.pathname + window.location.search)
    }
  }, [navigate])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<LoginResponse>('/v1/profile/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setSessionToken(data.session_token)
      setStoredProfile(data.profile)
      setStoredEmail(data.profile.email)
      clearSelectedPlan()
      setApiKeyExists(false)
      navigate('/select-plan', { replace: true })
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
          <p className="eyebrow">Authenticated access</p>
          <h1>Welcome back</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Enter your verified credentials to re-enter your workspace.
          </p>

          <div className="form-grid" style={{ marginBottom: '1.5rem' }}>
            <div>
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
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Password
              </label>
              <input
                required
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          </div>

          <Button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1rem' }}>
            {loading ? 'Signing in…' : 'Enter workspace'}
          </Button>

          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/signup" style={{ fontSize: '0.9rem' }}>Need an account? Sign up →</Link>
          </div>
          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/forgot-password" style={{ fontSize: '0.9rem' }}>Forgot password?</Link>
          </div>

          {error && <p className="error">{error}</p>}
        </form>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Workspace security" subtitle="What protects your account">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>Email-based verification</li>
              <li>Role-based access control</li>
              <li>Audit logs of all activity</li>
              <li>Secure session management</li>
              <li>Metadata-only data storage</li>
            </ul>
          </Card>

          <Card title="Your workspace includes" subtitle="What you get after login">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>Boundary protection dashboard</li>
              <li>Security event timeline</li>
              <li>API key management</li>
              <li>Team collaboration tools</li>
              <li>Compliance-ready exports</li>
            </ul>
          </Card>

          <Card title="Trouble signing in?" subtitle="We can help">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Email verification is required for all workspaces. Check your email for verification status.
            </p>
            <a href="mailto:support@maisb.app">
              <Button variant="secondary">Contact support</Button>
            </a>
          </Card>

          <div style={{ textAlign: 'center' }}>
            <Badge>
              🔒 All data is encrypted in transit and at rest
            </Badge>
          </div>
        </div>
      </div>
    </main>
  )
}
