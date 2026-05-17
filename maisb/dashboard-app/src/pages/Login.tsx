import { useState } from 'react'
import { setApiKey } from '../lib/auth'

export default function Login() {
  const [key, setKey] = useState('')
  return <main className="page"><h1>Login</h1><p>Use your API key to access dashboard pages.</p><input value={key} onChange={(e) => setKey(e.target.value)} placeholder="maisb_live_..." /><button onClick={() => { setApiKey(key); window.location.href = '/dashboard' }}>Continue</button></main>
}
