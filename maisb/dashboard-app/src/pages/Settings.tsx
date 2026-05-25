import { useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { clearAuthState, getStoredProfile } from '../lib/auth'

export default function Settings() {
  const profile = getStoredProfile()
  const [privacyMode, setPrivacyMode] = useState(true)
  const [tab, setTab] = useState<'profile' | 'privacy' | 'integrations'>('profile')

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Workspace settings</p>
          <h1>Settings</h1>
          <p className="muted">Clean workspace controls with a metadata-only posture.</p>
        </div>
        <Badge>Enterprise ready</Badge>
      </div>

      <Card
        title="Workspace configuration"
        actions={
          <div className="tab-strip">
            {(['profile', 'privacy', 'integrations'] as const).map((item) => (
              <button key={item} type="button" className={tab === item ? 'tab active' : 'tab'} onClick={() => setTab(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      >
        {tab === 'profile' && (
          <div className="grid two-col">
            <Card title="Profile details">
              <p><strong>Name:</strong> {profile?.name || '—'}</p>
              <p><strong>Email:</strong> {profile?.email || '—'}</p>
              <p><strong>Company:</strong> {profile?.company || '—'}</p>
            </Card>
            <Card title="Session hygiene">
              <p className="muted">Local session state is isolated to the browser and can be cleared at any time.</p>
              <Button variant="danger" onClick={clearAuthState}>Clear local session</Button>
            </Card>
          </div>
        )}

        {tab === 'privacy' && (
          <Card title="Privacy mode">
            <div className="split-row">
              <span>Privacy mode</span>
              <Button variant="secondary" onClick={() => setPrivacyMode((v) => !v)}>{privacyMode ? 'Enabled' : 'Disabled'}</Button>
            </div>
            <p className="muted">Payload retention policy: metadata only, no raw payload storage.</p>
          </Card>
        )}

        {tab === 'integrations' && (
          <Card title="Integrations">
            <p className="muted">Slack integration placeholder</p>
            <p className="muted">Webhook integration placeholder</p>
          </Card>
        )}
      </Card>
    </main>
  )
}
