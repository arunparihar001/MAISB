import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Badge from './Badge'
import Button from './Button'
import { clearAuthState, getApiKeyExists, getSelectedPlan, getStoredProfile } from '../lib/auth'

export default function Topbar() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const profile = getStoredProfile()
  const plan = getSelectedPlan() || 'unselected'

  return (
    <header className="topbar">
      <div>
        <strong>{profile?.company || 'MAISB Workspace'}</strong>
        <span>{profile?.email || 'security@workspace.local'}</span>
      </div>
      <div className="top-actions">
        <Badge>{plan.toUpperCase()}</Badge>
        <Badge>{getApiKeyExists() ? 'API Key Active' : 'API Key Missing'}</Badge>
        <div className="profile-menu">
          <Button variant="secondary" onClick={() => setOpen((value) => !value)}>
            {profile?.name || 'Profile'}
          </Button>
          {open && (
            <div className="profile-popover">
              <p className="muted">{profile?.email || 'No account loaded'}</p>
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
