import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { getApiKey, setStoredEmail } from '../lib/auth'

type LoginResponse = {
  profile_id: string
  email: string
  name?: string
  company?: string
  verified: boolean
  has_api_key: boolean
  next_step?: string
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // If already authenticated with a key, go straight to dashboard
  if (getApiKey()) {
    navigate('/dashboard', { replace: true })
    return null
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<LoginResponse>('/v1/profile/login', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setStoredEmail(data.email)
      navigate('/api-keys')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Sign in</h1>
        <p className="muted">Enter your work email to continue. You'll need a verified account.</p>
        <input
          required
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Work email"
        />
        <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Continue'}</button>
        <a href="/signup">Need an account? Sign up</a>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}

