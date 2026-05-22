import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setStoredEmail } from '../lib/auth'

type SignupResponse = {
  created: boolean
  email: string
  email_sent: boolean
}

export default function Signup() {
  const [form, setForm] = useState({ name: '', email: '', company: '', use_case: '', password: '' })
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<SignupResponse>('/v1/profile/signup', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setStoredEmail(data.email)
      setSubmitted(true)
    } catch (err) {
      setError((err as Error).message)
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
