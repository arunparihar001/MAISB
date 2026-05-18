import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setApiKey } from '../lib/auth'

type SignupResponse = {
  api_key: string
  api_key_masked: string
  warning: string
}

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [result, setResult] = useState<SignupResponse | null>(null)
  const [error, setError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      const response = await apiRequest<SignupResponse>('/v1/public/signup', { method: 'POST', body: form })
      setApiKey(response.api_key)
      setResult(response)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Signup failed')
    }
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={submit}>
        <h1>Create MAISB account</h1>
        <label>Email</label>
        <input required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label>Company</label>
        <input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <label>Name</label>
        <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <label>Use case</label>
        <textarea value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} />
        {error ? <p className="error">{error}</p> : null}
        <button className="btn" type="submit">Create API key</button>
        {result ? (
          <div className="notice">
            <p><strong>One-time API key:</strong> <span className="mono">{result.api_key}</span></p>
            <p>Masked key: <span className="mono">{result.api_key_masked}</span></p>
            <p className="warn">Copy and store this key securely. Do not commit it to source control.</p>
            <button type="button" className="btn" onClick={() => navigate('/dashboard')}>Continue to dashboard</button>
          </div>
        ) : null}
      </form>
    </main>
  )
}
