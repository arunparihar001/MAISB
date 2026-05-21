import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiRequest } from '../lib/api'

type VerifyResponse = { verified: boolean; email: string; profile_id: string; status: string }

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const [token, setToken] = useState(searchParams.get('token') || '')
  const [result, setResult] = useState<VerifyResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function verify(currentToken: string) {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<VerifyResponse>(`/v1/profile/verify-email?token=${encodeURIComponent(currentToken)}`)
      setResult(data)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (searchParams.get('token')) verify(searchParams.get('token') || '')
  }, [searchParams])

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!token.trim()) { setError('Verification token is required'); return }
    verify(token.trim())
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <h1>Verify your email</h1>
        {!result ? (
          <form onSubmit={onSubmit} className="stack compact">
            <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste verification token" />
            <button type="submit" disabled={loading}>{loading ? 'Verifying…' : 'Verify email'}</button>
          </form>
        ) : (
          <div className="card">
            <h3>Email verified</h3>
            <p>{result.email} is verified. You can now generate your API key.</p>
            <button onClick={() => navigate('/api-keys')}>Go to API keys</button>
          </div>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
