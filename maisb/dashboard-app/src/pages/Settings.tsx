import { FormEvent, useState } from 'react'
import { getAdminKey, setAdminKey } from '../lib/auth'

export default function Settings() {
  const [adminKey, updateAdminKey] = useState(getAdminKey())
  const [status, setStatus] = useState('')

  function saveSettings(event: FormEvent) {
    event.preventDefault()
    setAdminKey(adminKey)
    setStatus('Admin key updated in local storage.')
  }

  return (
    <form className="card form" onSubmit={saveSettings}>
      <h3>Settings</h3>
      <label htmlFor="adminKey">Admin bearer key for SOC endpoints</label>
      <input id="adminKey" type="password" value={adminKey} onChange={(e) => updateAdminKey(e.target.value)} />
      <button type="submit">Save</button>
      {status && <p className="notice">{status}</p>}
    </form>
  )
}
