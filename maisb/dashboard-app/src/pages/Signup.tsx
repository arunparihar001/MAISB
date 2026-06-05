import { FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest, type ApiError } from '../lib/api'
import { API_BASE_URL } from '../lib/config'
import { setStoredEmail } from '../lib/auth'

type SignupResponse = {
  created: boolean
  email: string
  email_sent: boolean
}

type SignupDiagnosticResult = { ok: true } | { ok: false; message: string }

const SIGNUP_DIAGNOSTICS_ENABLED = import.meta.env.DEV || import.meta.env.VITE_ENABLE_SIGNUP_DIAGNOSTICS === 'true'

async function runSignupDiagnostic(): Promise<SignupDiagnosticResult> {
  try {
    await apiRequest('/v1/profile/signup', {
      method: 'POST',
      body: JSON.stringify({}),
    })
    return { ok: true }
  } catch (err) {
    const apiError = err as ApiError
    if (typeof apiError.status === 'number') {
      if (apiError.status === 422) {
        return { ok: true }
      }
      return { ok: false, message: formatSignupError(apiError) }
    }
    return { ok: false, message: formatSignupError(err) }
  }
}

function formatSignupError(err: unknown): string {
  if (err instanceof Error) {
    const apiError = err as ApiError
    if (typeof apiError.status === 'number') {
      return `Signup API returned JSON error (${apiError.status}): ${err.message}`
    }
    return err.message
  }
  return `Network/CORS failure while calling POST /v1/profile/signup at ${API_BASE_URL}`
}

export default function Signup() {
  const [form, setForm] = useState({ name: '', email: '', company: '', use_case: '', password: '' })
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'blocked'>('checking')
  const diagnosticAttemptRef = useRef<Promise<SignupDiagnosticResult> | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function checkApi() {
      try {
        const response = await fetch(`${API_BASE_URL}/v1/cors-test`, {
          method: 'GET',
          mode: 'cors',
          signal: controller.signal,
          cache: 'no-store',
        })
        if (!response.ok) throw new Error('blocked')
        await response.json()
        setApiStatus('online')
      } catch {
        if (!controller.signal.aborted) setApiStatus('blocked')
      }
    }

    void checkApi()
    return () => controller.abort()
  }, [])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (SIGNUP_DIAGNOSTICS_ENABLED) {
        if (!diagnosticAttemptRef.current) {
          diagnosticAttemptRef.current = runSignupDiagnostic()
        }
        const diagnostic = await diagnosticAttemptRef.current
        if (!diagnostic.ok) {
          setError(diagnostic.message)
          diagnosticAttemptRef.current = null
          setLoading(false)
          return
        }
      }
      const data = await apiRequest<SignupResponse>('/v1/profile/signup', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setStoredEmail(data.email)
      setSubmitted(true)
    } catch (err) {
      setError(formatSignupError(err))
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <main className="onboarding-page">
        <div className="grid two-col" style={{ alignItems: 'center' }}>
          <div className="glass-card" style={{ padding: '2rem' }}>
            <p className="eyebrow">Signup complete</p>
            <h1>Verification email sent</h1>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              Check your inbox for the verification token. Complete email verification to unlock your workspace and start configuring boundary protection.
            </p>
            <p className="muted" style={{ marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              <strong>Security note:</strong> Email verification is required before workspace access. This protects your account from unauthorized signups.
            </p>
            <Link to="/verify-email"><Button>Go to verification →</Button></Link>
          </div>
          <Card title="What happens next?" subtitle="Your secure onboarding path">
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>1</span>
                <div>
                  <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Verify email</p>
                  <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Paste your token to confirm ownership</p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>2</span>
                <div>
                  <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Select plan</p>
                  <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Free plan starts immediately</p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>3</span>
                <div>
                  <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Generate API key</p>
                  <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Access /v1/scan endpoint immediately</p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ fontWeight: 'bold', color: '#67e8f9', minWidth: '1.5rem' }}>4</span>
                <div>
                  <p style={{ marginBottom: '0.25rem', fontWeight: 500 }}>Dashboard access</p>
                  <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>View analytics and security events</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </main>
    )
  }

  return (
    <main className="onboarding-page">
      <div className="grid two-col" style={{ alignItems: 'start', gap: '2rem' }}>
        <form className="glass-card" style={{ padding: '2rem' }} onSubmit={onSubmit}>
          <p className="eyebrow">Secure workspace onboarding</p>
          <h1>Create account</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Email verification is required. Your workspace is protected with role-based access and audit logs from day one.
          </p>
          
          <div className="form-grid" style={{ marginBottom: '1.5rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Full name
              </label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="John Doe"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Email address
              </label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Company
              </label>
              <input
                required
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Use case
              </label>
              <input
                required
                value={form.use_case}
                onChange={(e) => setForm({ ...form, use_case: e.target.value })}
                placeholder="Mobile AI assistant, fintech AI, etc."
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Password (min 8 characters)
              </label>
              <input
                required
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                minLength={8}
              />
            </div>
          </div>

          <Button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1rem' }}>
            {loading ? 'Creating…' : 'Create secure account'}
          </Button>

          <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <Link to="/login" style={{ fontSize: '0.9rem' }}>Already have an account? Login →</Link>
          </div>

          {apiStatus !== 'online' && (
            <p
              className={apiStatus === 'blocked' ? 'error' : ''}
              style={{
                fontSize: '0.85rem',
                marginBottom: '0.75rem',
                padding: '0.75rem',
                borderRadius: '12px',
                backgroundColor: apiStatus === 'blocked' ? 'rgba(127, 29, 29, 0.3)' : 'rgba(217, 119, 6, 0.3)',
              }}
              aria-live="polite"
              role="status"
            >
              API status: {apiStatus === 'blocked' ? '✗ Blocked or unreachable' : '⏳ Checking…'}
            </p>
          )}

          {error && <p className="error">{error}</p>}
        </form>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Why email verification?" subtitle="Security best practice">
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Verification ensures your account belongs to you. No one can access your workspace without your email confirmation token.
            </p>
          </Card>

          <Card title="Free tier includes" subtitle="Everything to get started">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>Boundary scans via /v1/scan API</li>
              <li>Dashboard with sample data</li>
              <li>API key generation and rotation</li>
              <li>Security event logging (30 days)</li>
              <li>Team invitation (single member)</li>
            </ul>
          </Card>

          <Card title="Workspace protection" subtitle="From day one">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>Role-based access (Admin, Analyst, Viewer)</li>
              <li>Audit trail of all actions</li>
              <li>Metadata-only event logging</li>
              <li>No raw payload storage</li>
              <li>Secure API key handling</li>
            </ul>
          </Card>

          <Card title="Questions?" subtitle="We're here to help">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Contact us at <a href="mailto:support@maisb.app">support@maisb.app</a>
            </p>
            <a href="/docs">
              <Button variant="secondary">View documentation →</Button>
            </a>
          </Card>
        </div>
      </div>
    </main>
  )
}
