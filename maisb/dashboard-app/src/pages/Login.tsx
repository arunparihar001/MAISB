import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
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
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Login</h1>
        <p className="muted">Use your verified account credentials.</p>
        <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
        <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Login'}</button>
        <Link to="/signup">Need an account? Sign up</Link>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}
