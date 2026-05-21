import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { getUserEmail, setUserEmail } from '../lib/auth'

type VerifyResponse = { verified: boolean; email: string; message: string }

export default function VerifyEmail() {
  const [email, setEmail] = useState(getUserEmail())
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const data = await apiRequest<VerifyResponse>('/v1/profile/verify-email', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), token: token.trim() }),
      })
      if (data.verified) {
        setUserEmail(email.trim())
        setMessage(data.message || 'Email verified!')
        setTimeout(() => navigate('/api-keys'), 1200)
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <h1>Verify your email</h1>
        <p>Enter the verification token sent to your inbox. Tokens expire after 24 hours.</p>
        <form onSubmit={onSubmit} className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
          <input
            required
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            required
            placeholder="Verification token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying…' : 'Verify email'}
          </button>
        </form>
        {message && <p className="notice">{message}</p>}
        {error && <p className="error">{error}</p>}
        <p>
          <a href="/signup">Resend verification email</a>
        </p>
      </section>
    </main>
  )
}
