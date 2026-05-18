import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { setApiKey } from '../lib/auth'

type SignupResponse = { api_key: string; api_key_masked: string; monthly_limit?: number; warning?: string }

export default function Signup() {
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [masked, setMasked] = useState('')
  const [warning, setWarning] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError('')
    try {
      const data = await apiRequest<SignupResponse>('/v1/public/signup', { method: 'POST', body: JSON.stringify({ ...form, tenant_id: 'default' }) })
      setApiKey(data.api_key)
      setMasked(data.api_key_masked)
      setWarning(data.warning || 'Copy/store this key securely. Do not commit it to GitHub or screenshots.')
    } catch (err) { setError((err as Error).message) } finally { setLoading(false) }
  }

  return (
    <main className="auth-page">
      <section className="auth-card wide">
        <h1>Create your API key</h1>
        {!masked ? (
          <form onSubmit={onSubmit} className="form-grid">
            <input required placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input placeholder="Use case" value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} />
            <button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create account'}</button>
          </form>
        ) : (
          <div className="card"><h3>Signup complete</h3><p>Masked key: <code>{masked}</code></p><p>{warning}</p><button onClick={() => navigate('/dashboard')}>Continue to dashboard</button></div>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
