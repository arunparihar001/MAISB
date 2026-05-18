import { useNavigate } from 'react-router-dom'
import { clearApiKey, getApiKey } from '../lib/auth'

function mask(value: string): string {
  if (!value) return 'Not signed in'
  if (value.length < 12) return '••••'
  return `${value.slice(0, 10)}••••${value.slice(-4)}`
}

export default function Topbar() {
  const navigate = useNavigate()
  return (
    <header className="topbar">
      <span>{mask(getApiKey())}</span>
      <button
        type="button"
        onClick={() => {
          clearApiKey()
          navigate('/login')
        }}
      >
        Logout
      </button>
    </header>
  )
}
