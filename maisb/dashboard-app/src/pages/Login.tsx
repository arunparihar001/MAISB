import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const navigate = useNavigate()
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!value.trim()) {
      setError('API key is required.')
      return
    }
    setApiKey(value)
    navigate('/dashboard')
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={submit}>
        <h1>Sign in to MAISB</h1>
        <p className="muted">Paste your API key to access the dashboard.</p>
        <label>API Key</label>
        <input value={value} onChange={(e) => setValue(e.target.value)} placeholder="maisb_live_..." />
        {error ? <p className="error">{error}</p> : null}
        <button className="btn" type="submit">Continue to dashboard</button>
      </form>
    </main>
  )
}
