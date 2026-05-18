import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = key.trim()
    if (!trimmed) {
      setError('API key is required')
      return
    }
    setApiKey(trimmed)
    navigate('/dashboard')
  }

  return (
    <main className="public-page">
      <h2>Login</h2>
      <form onSubmit={onSubmit}>
        <input value={key} onChange={(event) => setKey(event.target.value)} placeholder="maisb_live_..." />
        <button type="submit">Continue</button>
      </form>
      {error && <p className="error">{error}</p>}
    </main>
  )
}
