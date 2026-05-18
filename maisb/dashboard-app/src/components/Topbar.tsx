import { useNavigate } from 'react-router-dom'
import { clearApiKey, getApiKey, maskKey } from '../lib/auth'

export default function Topbar() {
  const navigate = useNavigate()
  return (
    <header className="topbar">
      <div>
        <p className="muted">Current API Key</p>
        <p className="mono">{maskKey(getApiKey())}</p>
      </div>
      <div className="topbar-actions">
        <button className="btn secondary" onClick={() => navigate('/settings')}>Settings</button>
        <button className="btn danger" onClick={() => { clearApiKey(); navigate('/login') }}>Logout</button>
      </div>
    </header>
  )
}
