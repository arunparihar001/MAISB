import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const [apiKey, setApiKeyInput] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }
    setApiKey(apiKey)
    navigate('/dashboard')
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={onSubmit}>
        <h1>Welcome back</h1>
        <label htmlFor="apiKey">API Key</label>
        <input id="apiKey" value={apiKey} onChange={(e) => setApiKeyInput(e.target.value)} type="password" />
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
        <p className="muted">Need an API key? <Link to="/signup">Create one</Link></p>
      </form>
    </main>
  )
}
