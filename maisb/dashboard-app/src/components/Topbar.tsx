import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from './Badge'
import Button from './Button'
import { clearAuthState, getApiKeyExists, getSelectedPlan, getStoredProfile } from '../lib/auth'

const ENV_STORAGE_KEY = 'maisb_dashboard_environment'
type Environment = 'Production' | 'Sandbox'

export default function Topbar() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [environment, setEnvironment] = useState<Environment>('Production')
  const profile = getStoredProfile()
  const plan = getSelectedPlan() || 'unselected'

  useEffect(() => {
    const stored = localStorage.getItem(ENV_STORAGE_KEY)
    if (stored === 'Production' || stored === 'Sandbox') {
      setEnvironment(stored)
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(ENV_STORAGE_KEY, environment)
  }, [environment])

  return (
    <header className="topbar">
      <div className="topbar-copy">
        <p className="eyebrow">Boundary control plane</p>
        <strong>{profile?.company || 'MAISB Workspace'}</strong>
        <span>{profile?.email || 'security@workspace.local'}</span>
      </div>
      <div className="top-actions">
        <label className="env-switcher">
          <span>Environment</span>
          <select value={environment} onChange={(event) => setEnvironment(event.target.value as Environment)}>
            <option>Production</option>
            <option>Sandbox</option>
          </select>
        </label>
        <Badge>{plan.toUpperCase()}</Badge>
        <Badge>{getApiKeyExists() ? 'Key Ready' : 'Key Missing'}</Badge>
        <Badge>Healthy</Badge>
        <div className="profile-menu">
          <Button variant="secondary" onClick={() => setOpen((value) => !value)}>
            {profile?.name || 'Profile'}
          </Button>
          {open && (
            <div className="profile-popover">
              <p className="popover-title">Workspace identity</p>
              <p className="muted">{profile?.email || 'No account loaded'}</p>
              <p className="muted">Environment: {environment}</p>
              <Button
                variant="danger"
                onClick={() => {
                  clearAuthState()
                  navigate('/login', { replace: true })
                }}
              >
                Sign out
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
