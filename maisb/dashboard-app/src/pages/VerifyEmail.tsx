import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiRequest } from '../lib/api'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setStatus('error')
      setMessage('No verification token found in the URL. Check the link in your email.')
      return
    }
    // POST the token in the body — never in the URL for security
    apiRequest<{ verified: boolean; email?: string }>('/v1/profile/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
      .then((data) => {
        setStatus('success')
        setMessage(data.email ? `${data.email} verified. You can now log in.` : 'Email verified. You can now log in.')
        setTimeout(() => navigate('/login'), 2500)
      })
      .catch((err: Error) => {
        setStatus('error')
        setMessage((err as Error).message || 'Verification failed. The token may have expired.')
      })
  }, [searchParams, navigate])

  return (
    <main className="auth-page">
      <div className="auth-card">
        {status === 'verifying' && (
          <>
            <h1>Verifying your email…</h1>
            <p>Please wait.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <h1>Email verified ✓</h1>
            <p>{message}</p>
            <p className="muted">Redirecting to login…</p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1>Verification failed</h1>
            <p className="error">{message}</p>
            <a href="/signup">Request a new verification link</a>
          </>
        )}
      </div>
    </main>
  )
}
