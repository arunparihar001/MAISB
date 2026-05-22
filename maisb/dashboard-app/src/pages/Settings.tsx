import { useState } from 'react'
import Button from '../components/Button'
import Card from '../components/Card'
import { clearAuthState, getStoredProfile } from '../lib/auth'

export default function Settings() {
  const profile = getStoredProfile()
  const [privacyMode, setPrivacyMode] = useState(true)

  return (
    <main className="stack">
      <h1>Settings</h1>
      <Card title="Profile details">
        <p><strong>Name:</strong> {profile?.name || '—'}</p>
        <p><strong>Email:</strong> {profile?.email || '—'}</p>
        <p><strong>Company:</strong> {profile?.company || '—'}</p>
      </Card>
      <Card title="Privacy mode">
        <div className="split-row">
          <span>Privacy mode</span>
          <Button variant="secondary" onClick={() => setPrivacyMode((v) => !v)}>{privacyMode ? 'Enabled' : 'Disabled'}</Button>
        </div>
        <p className="muted">Payload retention policy: metadata only, no raw payload storage.</p>
      </Card>
      <Card title="Integrations">
        <p className="muted">Slack integration placeholder</p>
        <p className="muted">Webhook integration placeholder</p>
      </Card>
      <Card>
        <Button variant="danger" onClick={clearAuthState}>Clear local session</Button>
      </Card>
    </main>
  )
}
