import { FormEvent, useState } from 'react'
import { apiRequest } from '../lib/api'
import { setStoredEmail } from '../lib/auth'

type SignupResponse = { profile_id: string; email: string; email_sent: boolean; next_step?: string }

export default function Signup() {
  const [form, setForm] = useState({ name: '', email: '', company: '', use_case: '' })
  const [submitted, setSubmitted] = useState(false)
  const [emailSent, setEmailSent] = useState(false)
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
      setEmailSent(data.email_sent)
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
          <h1>Check your inbox</h1>
          <p>
            {emailSent
              ? `A verification link was sent to ${form.email}. Click it to confirm your account.`
              : `We received your sign-up for ${form.email}. Check your inbox for a verification link.`}
          </p>
          <p className="muted">After verifying, return here to <a href="/login">log in</a>.</p>
        </div>
      </main>
    )
  }

  return (
    <main className="auth-page">
      <section className="auth-card wide">
        <h1>Create your account</h1>
        <p className="muted">Enter your details. We'll send a verification link to your email.</p>
        <form onSubmit={onSubmit} className="form-grid">
          <input
            required
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            required
            type="email"
            placeholder="Work email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            placeholder="Company (optional)"
            value={form.company}
            onChange={(e) => setForm({ ...form, company: e.target.value })}
          />
          <input
            placeholder="Use case (optional)"
            value={form.use_case}
            onChange={(e) => setForm({ ...form, use_case: e.target.value })}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Sending…' : 'Create account'}
          </button>
        </form>
        <p className="muted">Already have an account? <a href="/login">Log in</a></p>
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}

