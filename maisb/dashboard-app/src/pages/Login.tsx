import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = key.trim()
    if (!trimmed) { setError('API key is required'); return }
    setApiKey(trimmed)
    navigate('/dashboard')
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Access MAISB dashboard</h1><p>Paste your verified MAISB API key. It is stored locally in this browser for this MVP experience.</p>
        <input value={key} onChange={(e) => setKey(e.target.value)} placeholder="maisb_live_..." />
        <button type="submit">Continue</button>
        <a href="/signup">Need access? Create profile</a>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}
