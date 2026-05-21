import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../lib/api'

type SignupResponse = { profile_id: string; email: string; status: string; verification_email_sent: boolean }

export default function Signup() {
  const [form, setForm] = useState({ email: '', company: '', name: '', use_case: '' })
  const [profile, setProfile] = useState<SignupResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function onSubmit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError('')
    try {
      const data = await apiRequest<SignupResponse>('/v1/profile/signup', { method: 'POST', body: JSON.stringify(form) })
      setProfile(data)
    } catch (err) { setError((err as Error).message) } finally { setLoading(false) }
  }

  return (
    <main className="auth-page">
      <section className="auth-card wide">
        <h1>Create your MAISB profile</h1>
        {!profile ? (
          <form onSubmit={onSubmit} className="form-grid">
            <input required placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <input placeholder="Use case" value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} />
            <button type="submit" disabled={loading}>{loading ? 'Submitting…' : 'Create profile'}</button>
          </form>
        ) : (
          <div className="card"><h3>Check your email to verify</h3><p>Profile: <code>{profile.profile_id}</code></p><p>Email: <code>{profile.email}</code></p><p>Verification email status: {profile.verification_email_sent ? 'sent' : 'not configured in environment'}</p><button onClick={() => navigate('/verify-email')}>Continue to email verification</button></div>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
