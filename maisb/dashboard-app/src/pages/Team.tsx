import { FormEvent, useEffect, useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import DataTable from '../components/DataTable'
import { apiRequest } from '../lib/api'

type TeamMember = { member_id: string; email: string; name?: string; role: string; status: string }

type TeamResponse = { team: TeamMember[]; enterprise_actions?: { coming_soon?: boolean } }

type Invite = { invited: boolean; email: string; role: string; invite_id: string; status: string; message: string }

export default function Team() {
  const [team, setTeam] = useState<TeamMember[]>([])
  const [comingSoon, setComingSoon] = useState(false)
  const [tab, setTab] = useState<'members' | 'roles' | 'activity'>('members')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('analyst')
  const [activity, setActivity] = useState<Array<{ id: string; entry: string }>>([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    apiRequest<TeamResponse>('/v1/team')
      .then((data) => {
        setTeam(data.team || [])
        setComingSoon(Boolean(data.enterprise_actions?.coming_soon))
      })
      .catch(() => {
        setTeam([])
        setComingSoon(true)
      })
  }, [])

  async function onInvite(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      const data = await apiRequest<Invite>('/v1/team/invite', {
        method: 'POST',
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      })
      setActivity((items) => [{ id: data.invite_id, entry: `Invited ${data.email} as ${data.role} (${data.status})` }, ...items])
      setMessage(data.message)
      setInviteEmail('')
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  const roleDescriptions: Record<string, string> = {
    admin: 'Full workspace control. Can invite members, manage API keys, configure settings, and revoke access.',
    analyst: 'Can view events, review traces, generate reports, and invite other analysts. Cannot modify workspace settings.',
    viewer: 'Read-only access. Can view dashboard, analytics, security events, and reports. Cannot modify anything.',
  }

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Enterprise permissions</p>
          <h1>Team</h1>
          <p className="muted">Invite team members with role-based access controls. Audit activity and manage permissions.</p>
        </div>
        <Badge>{comingSoon ? 'Controls staged rollout' : 'Access online'}</Badge>
      </div>

      <Card
        title="Team console"
        actions={
          <div className="tab-strip">
            {(['members', 'roles', 'activity'] as const).map((item) => (
              <button key={item} type="button" className={tab === item ? 'tab active' : 'tab'} onClick={() => setTab(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      >
        {tab === 'members' && (
          <div className="grid two-col">
            <form onSubmit={onInvite} className="form-grid card-inset">
              <h3>Invite team member</h3>
              <input
                required
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
              />
              <div>
                <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                  Role
                </label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                  <option value="admin">Admin</option>
                  <option value="analyst">Analyst</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
                {roleDescriptions[inviteRole]}
              </div>
              <Button type="submit">Send invite</Button>
            </form>
            <div className="card-inset">
              <p className="eyebrow">Current team members</p>
              {team.length > 0 ? (
                <DataTable
                  columns={[
                    { key: 'name', label: 'Name', render: (row) => row.name || row.email },
                    { key: 'role', label: 'Role', render: (row) => <Badge>{row.role}</Badge> },
                    { key: 'status', label: 'Status', render: (row) => (
                      <span style={{ fontSize: '0.85rem', color: row.status === 'active' ? '#86efac' : '#fbbf24' }}>
                        {row.status}
                      </span>
                    ) },
                  ]}
                  rows={team}
                  rowKey={(row) => row.member_id}
                />
              ) : (
                <p className="muted">No team members yet. Invite your first team member above.</p>
              )}
            </div>
          </div>
        )}

        {tab === 'roles' && (
          <div className="grid two-col">
            <Card title="Admin" subtitle="Full workspace control">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                Admins have complete control over the workspace. They can:
              </p>
              <ul className="bullet-list" style={{ margin: 0, marginTop: '0.75rem' }}>
                <li>Invite and remove team members</li>
                <li>Change member roles</li>
                <li>Create and revoke API keys</li>
                <li>Configure workspace settings</li>
                <li>Access billing and upgrade options</li>
                <li>View all security events and traces</li>
                <li>Generate compliance reports</li>
              </ul>
            </Card>

            <Card title="Analyst" subtitle="Security operations">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                Analysts focus on security operations and review. They can:
              </p>
              <ul className="bullet-list" style={{ margin: 0, marginTop: '0.75rem' }}>
                <li>View all security events and traces</li>
                <li>Review blocked and flagged scans</li>
                <li>Generate reports and exports</li>
                <li>Invite other analysts and viewers</li>
                <li>Access analytics and dashboards</li>
                <li>Cannot modify API keys or settings</li>
                <li>Cannot manage team members</li>
              </ul>
            </Card>

            <Card title="Viewer" subtitle="Read-only access">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                Viewers have read-only access to the dashboard and reports. They can:
              </p>
              <ul className="bullet-list" style={{ margin: 0, marginTop: '0.75rem' }}>
                <li>View dashboard and KPIs</li>
                <li>View security events and traces</li>
                <li>View analytics and reports</li>
                <li>View team members and roles</li>
                <li>Cannot make any modifications</li>
                <li>Cannot invite team members</li>
                <li>Perfect for executives and auditors</li>
              </ul>
            </Card>

            <Card title="Coming soon" subtitle="Advanced role controls">
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                Enterprise plan will include:
              </p>
              <ul className="bullet-list" style={{ margin: 0, marginTop: '0.75rem' }}>
                <li>Custom role definitions</li>
                <li>Scoped workspace administration</li>
                <li>Least-privilege access reviews</li>
                <li>SSO and directory integration</li>
                <li>Audit trail for permission changes</li>
              </ul>
            </Card>
          </div>
        )}

        {tab === 'activity' && (
          <div>
            <Card title="Team activity log">
              {activity.length > 0 ? (
                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  {activity.map((item, index) => (
                    <div
                      key={item.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.75rem',
                        borderBottom: index < activity.length - 1 ? '1px solid rgba(148, 163, 184, 0.12)' : 'none',
                        fontSize: '0.9rem',
                      }}
                    >
                      <span className="muted">{item.entry}</span>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{new Date().toLocaleDateString()}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No activity yet. Invite your first team member to start logging activity.</p>
              )}
            </Card>
          </div>
        )}
      </Card>

      {message && <p className="notice">{message}</p>}
    </main>
  )
}
