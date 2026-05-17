import { useState } from 'react'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const [key, setKey] = useState('')

  const submit = () => {
    if (!key.trim()) return
    setApiKey(key)
    window.location.href = '/dashboard'
  }

  return (
    <main className="page auth-page">
      <h1>Customer Login</h1>
      <p>Enter your MAISB API key to access usage, billing, and certification workflows.</p>
      <input value={key} onChange={(e) => setKey(e.target.value)} placeholder="maisb_live_..." />
      <button onClick={submit}>Continue to Dashboard</button>
    </main>
  )
}
