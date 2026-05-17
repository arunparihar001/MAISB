import { useState } from 'react'
import { apiPost } from '../lib/api'
import { setApiKey } from '../lib/auth'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')
  const [message, setMessage] = useState('')
  const submit = async () => {
    try {
      const data = await apiPost<{ api_key: string; api_key_masked: string }>('/v1/public/signup', { email, company })
      setApiKey(data.api_key)
      setMessage(`API key created: ${data.api_key_masked}`)
    } catch {
      setMessage('Signup failed. Please verify email and try again.')
    }
  }
  return <main className="page"><h1>Signup</h1><input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" /><input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company" /><button onClick={submit}>Create account</button><p>{message}</p></main>
}
