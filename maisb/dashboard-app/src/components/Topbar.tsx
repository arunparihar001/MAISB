import { useNavigate } from 'react-router-dom'
import { clearApiKey, getApiKey, maskSecret } from '../lib/auth'

export default function Topbar() {
  const navigate = useNavigate()
  return (
    <header className="topbar">
      <div>
        <strong>MAISB Dashboard</strong>
        <span>AI Runtime Security for Mobile & Fintech Applications</span>
      </div>
      <div className="top-actions">
        <code>{maskSecret(getApiKey())}</code>
        <button
          type="button"
          className="secondary"
          onClick={() => {
            clearApiKey()
            navigate('/login')
          }}
        >
          Logout
        </button>
      </div>
    </header>
  )
}
