import { Link, useNavigate } from 'react-router-dom'
import { clearAdminKey, clearApiKey } from '../lib/auth'

export default function Topbar({ apiKeyMasked }: { apiKeyMasked: string }) {
  const navigate = useNavigate()
  function logout() {
    clearApiKey()
    clearAdminKey()
    navigate('/login')
  }
  return (
    <header className="topbar">
      <span className="pill">Key: {apiKeyMasked || 'Not loaded'}</span>
      <div className="topbar-actions">
        <Link to="/settings">Settings</Link>
        <button onClick={logout}>Logout</button>
      </div>
    </header>
  )
}
