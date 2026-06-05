import { useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { clearAuthState, getStoredProfile } from '../lib/auth'

export default function Settings() {
  const profile = getStoredProfile()
  const [privacyMode, setPrivacyMode] = useState(true)
  const [tab, setTab] = useState<'profile' | 'privacy' | 'integrations' | 'danger'>('profile')

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Workspace settings</p>
          <h1>Settings</h1>
          <p className="muted">Clean workspace controls with metadata-only posture and fine-grained permissions.</p>
        </div>
        <Badge>Enterprise ready</Badge>
      </div>

      <Card
        title="Workspace configuration"
        actions={
          <div className="tab-strip">
            {(['profile', 'privacy', 'integrations', 'danger'] as const).map((item) => (
              <button key={item} type="button" className={tab === item ? 'tab active' : 'tab'} onClick={() => setTab(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      >
        {tab === 'profile' && (
          <div className="grid two-col">
            <Card title="Profile details" subtitle="Workspace identity">
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Name</p>
                  <p>{profile?.name || '—'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Email</p>
                  <p>{profile?.email || '—'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Company</p>
                  <p>{profile?.company || '—'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Verification status</p>
                  <Badge>{profile?.verified ? 'Verified' : 'Pending'}</Badge>
                </div>
              </div>
            </Card>

            <Card title="Workspace info" subtitle="Current entitlements">
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Plan</p>
                  <Badge>{profile?.plan || 'Free'}</Badge>
                </div>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Member count</p>
                  <p>1</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>API keys active</p>
                  <p>2</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {tab === 'privacy' && (
          <div className="grid">
            <Card title="Data retention policy" subtitle="Metadata-only architecture">
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span>Metadata-only mode</span>
                    <span style={{ fontSize: '0.85rem', color: '#86efac' }}>Always enabled</span>
                  </div>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>
                    Raw payloads are never stored. Only channel, timestamp, risk score, and decision are logged.
                  </p>
                </div>
              </div>
            </Card>

            <Card title="Payload retention" subtitle="What we store and for how long">
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Free tier</p>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>30-day retention. Metadata only.</p>
                </div>
                <div>
                  <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Pro/Enterprise</p>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>90+ day retention. Configurable. Metadata only.</p>
                </div>
                <div>
                  <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Export policy</p>
                  <p className="muted" style={{ fontSize: '0.9rem' }}>CSV/JSON exports never include raw content. Only audit evidence.</p>
                </div>
              </div>
            </Card>

            <Card title="Privacy controls" subtitle="What you control">
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Privacy mode</span>
                  <Button
                    variant="secondary"
                    onClick={() => setPrivacyMode((v) => !v)}
                    style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem' }}
                  >
                    {privacyMode ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                <p className="muted" style={{ fontSize: '0.85rem' }}>
                  {privacyMode
                    ? 'Privacy mode is enabled. Redacted previews are used in event tables.'
                    : 'Privacy mode is disabled. Full content hashes may appear in exports.'}
                </p>
              </div>
            </Card>

            <Card title="Audit trail" subtitle="Who accessed what and when">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                All API calls, team invites, and security decisions are logged with timestamp, user, and action. Access the audit trail in the Team section.
              </p>
            </Card>
          </div>
        )}

        {tab === 'integrations' && (
          <div className="grid">
            <Card title="Slack integration" subtitle="Security alerts and reports">
              <p className="muted">Direct Slack notifications for critical security events, blocked scans, and compliance reports.</p>
              <div style={{ marginTop: '1rem' }}>
                <Badge>Coming soon</Badge>
              </div>
            </Card>

            <Card title="Webhook integration" subtitle="Custom webhooks for automation">
              <p className="muted">Send security events, traces, and reports to your own systems. Custom webhook configuration and filtering.</p>
              <div style={{ marginTop: '1rem' }}>
                <Badge>Coming soon</Badge>
              </div>
            </Card>

            <Card title="SSO integration" subtitle="Enterprise directory sync">
              <p className="muted">SAML 2.0 and OIDC support for team member provisioning. Available on Enterprise plan.</p>
              <div style={{ marginTop: '1rem' }}>
                <Badge>Enterprise only</Badge>
              </div>
            </Card>

            <Card title="API access" subtitle="Programmatic workspace management">
              <p className="muted">Full API for automation. Create API keys, manage team, export reports, and more via our REST API.</p>
              <div style={{ marginTop: '1rem' }}>
                <a href="/docs/api">
                  <Button variant="secondary">View API docs</Button>
                </a>
              </div>
            </Card>
          </div>
        )}

        {tab === 'danger' && (
          <div className="grid">
            <Card title="Session management" subtitle="Clear local session data">
              <p className="muted">Clear your session from this browser. You will be logged out and will need to log back in.</p>
              <div style={{ marginTop: '1rem' }}>
                <Button
                  variant="secondary"
                  onClick={clearAuthState}
                >
                  Clear local session
                </Button>
              </div>
            </Card>

            <Card title="Workspace deletion" subtitle="Permanently remove this workspace">
              <p className="muted">Deleting a workspace will permanently remove all data, settings, team members, and API keys. This action cannot be undone.</p>
              <div style={{ marginTop: '1rem' }}>
                <Button variant="danger" disabled>
                  Delete workspace
                </Button>
              </div>
              <p className="muted" style={{ fontSize: '0.85rem', marginTop: '0.75rem' }}>
                Contact support@maisb.app to request workspace deletion.
              </p>
            </Card>

            <Card title="Data export" subtitle="Export all your data">
              <p className="muted">Export your workspace configuration, team settings, and security event history in JSON format.</p>
              <div style={{ marginTop: '1rem' }}>
                <Button variant="secondary" disabled>
                  Export workspace
                </Button>
              </div>
              <p className="muted" style={{ fontSize: '0.85rem', marginTop: '0.75rem' }}>
                Coming soon. Contact support@maisb.app to request a data export.
              </p>
            </Card>
          </div>
        )}
      </Card>
    </main>
  )
}
