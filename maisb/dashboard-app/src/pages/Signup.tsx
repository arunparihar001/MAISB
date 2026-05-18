import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setApiKey } from '../lib/auth'

type SignupResponse = {
  api_key: string
  api_key_masked: string
}

export default function Signup() {
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [masked, setMasked] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [ready, setReady] = useState(false)

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest<SignupResponse>('/v1/public/signup', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setMasked(data.api_key_masked)
      setApiKey(data.api_key)
      setReady(true)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="public-page">
      <h2>Signup</h2>
      {!ready ? (
        <form onSubmit={onSubmit}>
          <input required placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          <input placeholder="Company" value={form.company} onChange={(event) => setForm({ ...form, company: event.target.value })} />
          <input placeholder="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          <input placeholder="Use case" value={form.use_case} onChange={(event) => setForm({ ...form, use_case: event.target.value })} />
          <button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create account'}</button>
        </form>
      ) : (
        <div className="card">
          <p>Signup complete.</p>
          <p>API key: {masked}</p>
          <button type="button" onClick={() => navigate('/dashboard')}>Continue to dashboard</button>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </main>
  )
}
