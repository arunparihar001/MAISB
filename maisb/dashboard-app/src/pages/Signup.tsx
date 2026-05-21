import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setUserEmail } from '../lib/auth'

type SignupResponse = { created: boolean; email: string; next_step: string; email_delivery: string }

export default function Signup() {
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<SignupResponse>('/v1/profile/signup', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      if (data.created) {
        setUserEmail(form.email.trim())
        setSent(true)
        setTimeout(() => navigate('/verify-email'), 1800)
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card wide">
        <h1>Create your MAISB Shield account</h1>
        {!sent ? (
          <form onSubmit={onSubmit} className="form-grid">
            <input
              required
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <input
              placeholder="Full name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
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
        ) : (
          <div className="card">
            <h3>Check your inbox</h3>
            <p>
              A verification email has been sent to <strong>{form.email}</strong>.
              Enter the token on the next page to complete your account setup.
            </p>
            <button onClick={() => navigate('/verify-email')}>Continue to verification</button>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        <p>
          Already have an account? <a href="/login">Log in</a>
        </p>
      </section>
    </main>
  )
}
