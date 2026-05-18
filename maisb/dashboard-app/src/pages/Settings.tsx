import { useState } from 'react'
import { clearAdminKey, clearApiKey, getAdminKey, getApiKey, maskKey, setAdminKey } from '../lib/auth'

export default function Settings() {
  const [adminInput, setAdminInput] = useState(getAdminKey())
  const [saved, setSaved] = useState('')

  return (
    <section className="stack">
      <h1>Settings</h1>
      <section className="card">
        <h3>Current API Key</h3>
        <p className="mono">{maskKey(getApiKey())}</p>
        <button className="btn danger" onClick={() => clearApiKey()}>Clear API key</button>
      </section>
      <section className="card form">
        <h3>SOC Admin Key</h3>
        <input value={adminInput} onChange={(e) => setAdminInput(e.target.value)} placeholder="Bearer admin key" />
        <div className="row">
          <button className="btn" onClick={() => { setAdminKey(adminInput); setSaved('Admin key saved locally.') }}>Save admin key</button>
          <button className="btn secondary" onClick={() => { clearAdminKey(); setAdminInput(''); setSaved('Admin key cleared.') }}>Clear</button>
        </div>
        {saved ? <p className="muted">{saved}</p> : null}
      </section>
    </section>
  )
}
