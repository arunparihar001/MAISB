import { FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
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
    return { ok: true as const }
  } catch (err) {
    const apiError = err as ApiError
    if (typeof apiError.status === 'number') {
      if (apiError.status === 422) {
        return { ok: true as const }
      }
      return {
        ok: false as const,
        message: `Signup API returned JSON error (${apiError.status}): ${apiError.message}`,
      }
    }
    return {
      ok: false as const,
      message: err instanceof Error ? err.message : `Network/CORS failure while calling POST /v1/profile/signup at ${API_BASE_URL}`,
    }
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
      <main className="auth-page">
        <div className="auth-card">
          <h1>Verification email sent</h1>
          <p className="muted">Check your inbox for the token, then complete verification.</p>
          <Link to="/verify-email">Verify email</Link>
        </div>
      </main>
    )
  }

  return (
    <main className="auth-page">
      <form className="auth-card wide" onSubmit={onSubmit}>
        <h1>Create account</h1>
        <p className="muted">Enterprise workspace onboarding starts with email verification.</p>
        <p className="muted" aria-live="polite" role="status">
          API base: {API_BASE_URL} · API status: {apiStatus === 'online' ? 'Online' : apiStatus === 'blocked' ? 'API blocked or unreachable' : 'Checking…'}
        </p>
        <div className="form-grid">
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" />
          <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" />
          <input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="Company" />
          <input required value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} placeholder="Use case" />
          <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Password (min 8 chars)" minLength={8} />
        </div>
        <button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Sign up'}</button>
        <Link to="/login">Already have an account? Login</Link>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}
