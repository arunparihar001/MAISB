import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setApiKey } from '../lib/auth'

interface SignupResponse {
  api_key: string
  api_key_masked: string
  warning: string
}

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [result, setResult] = useState<SignupResponse | null>(null)
  const [error, setError] = useState('')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const response = await apiRequest<SignupResponse>('/v1/public/signup', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setApiKey(response.api_key)
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
    }
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={onSubmit}>
        <h1>Create API Key</h1>
        <input placeholder="Work email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <textarea placeholder="Use case" value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} />
        <button type="submit">Create key</button>
        {error && <p className="error">{error}</p>}
        {result && (
          <div className="notice">
            <p>Masked key: {result.api_key_masked}</p>
            <p>{result.warning}</p>
            <button type="button" onClick={() => navigate('/dashboard')}>Continue to dashboard</button>
          </div>
        )}
      </form>
    </main>
  )
}
